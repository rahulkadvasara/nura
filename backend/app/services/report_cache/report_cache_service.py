"""
Nura - Report Cache Service
TTL-based caching for OCR results, chunk embeddings, and AI summaries.
Follows the same pattern as RAGCacheService. Cache invalidation on report update.
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nura.report_cache")

# Default TTLs (seconds)
OCR_CACHE_TTL = 86400       # 24 hours
EMBEDDING_CACHE_TTL = 43200  # 12 hours
SUMMARY_CACHE_TTL = 21600    # 6 hours


def _file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content for OCR cache keying."""
    return hashlib.sha256(content).hexdigest()


def _text_hash(text: str) -> str:
    """Compute SHA-256 hash of text for embedding cache keying."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ReportCacheService:
    """
    Dedicated caching layer for the report processing pipeline.

    Three cache types:
    - OCR cache: keyed by file content hash — skips re-OCR on identical files
    - Embedding cache: keyed by text chunk hash — reuses embeddings across re-syncs
    - Summary cache: keyed by (report_id, summary_version) — skips AI calls on unchanged versions

    All caches use in-memory TTL dicts. Cache invalidation clears all entries for a report_id.
    """

    def __init__(
        self,
        ocr_ttl: int = OCR_CACHE_TTL,
        embedding_ttl: int = EMBEDDING_CACHE_TTL,
        summary_ttl: int = SUMMARY_CACHE_TTL,
    ):
        self.ocr_ttl = ocr_ttl
        self.embedding_ttl = embedding_ttl
        self.summary_ttl = summary_ttl

        # {file_hash: (timestamp, ocr_result_dict)}
        self._ocr_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        # {text_hash: (timestamp, embedding_vector)}
        self._embedding_cache: Dict[str, Tuple[float, List[float]]] = {}
        # {(report_id, version): (timestamp, summary_text)}
        self._summary_cache: Dict[str, Tuple[float, str]] = {}
        # Track which file_hashes belong to which report_id (for invalidation)
        self._report_file_hashes: Dict[str, str] = {}   # report_id → file_hash
        self._report_text_hashes: Dict[str, List[str]] = {}  # report_id → [text_hash, ...]

    # ------------------------------------------------------------------
    # OCR Cache
    # ------------------------------------------------------------------

    def get_ocr(self, file_content: bytes) -> Optional[Dict[str, Any]]:
        """Return cached OCR result for the given file content, or None if not cached / expired."""
        key = _file_hash(file_content)
        if key in self._ocr_cache:
            ts, val = self._ocr_cache[key]
            if time.time() - ts <= self.ocr_ttl:
                logger.debug(f"OCR cache HIT for file hash {key[:12]}")
                return val
            del self._ocr_cache[key]
        logger.debug(f"OCR cache MISS for file hash {key[:12]}")
        return None

    def set_ocr(self, file_content: bytes, result: Dict[str, Any], report_id: Optional[str] = None) -> None:
        """Cache OCR result for the given file content."""
        key = _file_hash(file_content)
        self._ocr_cache[key] = (time.time(), result)
        if report_id:
            self._report_file_hashes[report_id] = key

    def get_ocr_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Return cached OCR result by pre-computed file hash."""
        if file_hash in self._ocr_cache:
            ts, val = self._ocr_cache[file_hash]
            if time.time() - ts <= self.ocr_ttl:
                return val
            del self._ocr_cache[file_hash]
        return None

    # ------------------------------------------------------------------
    # Embedding Cache
    # ------------------------------------------------------------------

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Return cached embedding vector for the given text chunk."""
        key = _text_hash(text)
        if key in self._embedding_cache:
            ts, val = self._embedding_cache[key]
            if time.time() - ts <= self.embedding_ttl:
                logger.debug(f"Embedding cache HIT for text hash {key[:12]}")
                return val
            del self._embedding_cache[key]
        logger.debug(f"Embedding cache MISS for text hash {key[:12]}")
        return None

    def set_embedding(self, text: str, vector: List[float], report_id: Optional[str] = None) -> None:
        """Cache embedding vector for the given text chunk."""
        key = _text_hash(text)
        self._embedding_cache[key] = (time.time(), vector)
        if report_id:
            self._report_text_hashes.setdefault(report_id, []).append(key)

    # ------------------------------------------------------------------
    # Summary Cache
    # ------------------------------------------------------------------

    def get_summary(self, report_id: str, version: int = 1) -> Optional[str]:
        """Return cached AI summary for the given report and version."""
        key = f"{report_id}::v{version}"
        if key in self._summary_cache:
            ts, val = self._summary_cache[key]
            if time.time() - ts <= self.summary_ttl:
                logger.debug(f"Summary cache HIT for {key}")
                return val
            del self._summary_cache[key]
        logger.debug(f"Summary cache MISS for {report_id} v{version}")
        return None

    def set_summary(self, report_id: str, summary: str, version: int = 1) -> None:
        """Cache AI summary for the given report and version."""
        key = f"{report_id}::v{version}"
        self._summary_cache[key] = (time.time(), summary)

    # ------------------------------------------------------------------
    # Cache Invalidation
    # ------------------------------------------------------------------

    def invalidate_report(self, report_id: str) -> None:
        """
        Clear all cache entries associated with a specific report.
        Called when report content changes (e.g. re-upload or reprocessing).
        """
        # Remove OCR cache entry
        file_hash = self._report_file_hashes.pop(report_id, None)
        if file_hash and file_hash in self._ocr_cache:
            del self._ocr_cache[file_hash]
            logger.info(f"Invalidated OCR cache for report {report_id}")

        # Remove embedding cache entries
        text_hashes = self._report_text_hashes.pop(report_id, [])
        for th in text_hashes:
            self._embedding_cache.pop(th, None)
        if text_hashes:
            logger.info(f"Invalidated {len(text_hashes)} embedding cache entries for report {report_id}")

        # Remove summary cache entries (all versions)
        keys_to_remove = [k for k in self._summary_cache if k.startswith(f"{report_id}::")]
        for k in keys_to_remove:
            del self._summary_cache[k]
        if keys_to_remove:
            logger.info(f"Invalidated {len(keys_to_remove)} summary cache versions for report {report_id}")

    def prune_expired(self) -> Dict[str, int]:
        """Remove all expired entries from all caches. Returns pruned counts per cache type."""
        now = time.time()
        pruned = {"ocr": 0, "embedding": 0, "summary": 0}

        for cache, ttl, key in [
            (self._ocr_cache, self.ocr_ttl, "ocr"),
            (self._embedding_cache, self.embedding_ttl, "embedding"),
            (self._summary_cache, self.summary_ttl, "summary"),
        ]:
            for k in list(cache.keys()):
                ts, _ = cache[k]
                if now - ts > ttl:
                    del cache[k]
                    pruned[key] += 1

        return pruned

    def get_stats(self) -> Dict[str, Any]:
        """Return cache size statistics."""
        return {
            "ocr": {"size": len(self._ocr_cache), "ttl_seconds": self.ocr_ttl},
            "embedding": {"size": len(self._embedding_cache), "ttl_seconds": self.embedding_ttl},
            "summary": {"size": len(self._summary_cache), "ttl_seconds": self.summary_ttl},
        }

    def clear(self) -> None:
        """Clear all caches (use for testing only)."""
        self._ocr_cache.clear()
        self._embedding_cache.clear()
        self._summary_cache.clear()
        self._report_file_hashes.clear()
        self._report_text_hashes.clear()
