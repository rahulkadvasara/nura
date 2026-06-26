"""
Nura - Retrieval Service
Handles semantic search, metadata-aware filtering, multi-collection querying, score normalization, deduplication, and search statistics tracking.
"""

import time
import logging
import asyncio
from typing import List, Dict, Any, Optional

from app.core.ai_config import AISettings, ai_settings
from app.core.vector_collections import get_collection_for_document_type
from app.core.constants import QDRANT_COLLECTIONS
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.vector_service import VectorService, get_vector_service
from app.utils.ai import retrieval_metrics

logger = logging.getLogger("nura.ai.retrieval")


def resolve_collection_name(name_or_type: str) -> str:
    """
    Resolve a document type identifier (e.g. REPORT) or direct collection name 
    (e.g. patient_reports) to its standard Qdrant collection name.
    """
    cleaned = name_or_type.upper().strip()
    try:
        return get_collection_for_document_type(cleaned)
    except ValueError:
        pass

    lower_val = name_or_type.lower().strip()
    for col_val in QDRANT_COLLECTIONS.values():
        if col_val == lower_val:
            return col_val

    raise ValueError(f"Unknown target collection or document type identifier: '{name_or_type}'")


class RetrievalService:
    """Core Retrieval Service for executing metadata-aware vector search across collections"""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_service: VectorService,
        settings: AISettings = ai_settings
    ):
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.settings = settings

    def normalize_score(self, score: float) -> float:
        """
        Normalize raw cosine similarity score from [-1.0, 1.0] to [0.0, 1.0] range.
        Formula: (raw_score + 1.0) / 2.0
        """
        return float(max(0.0, min(1.0, (score + 1.0) / 2.0)))

    def _translate_filters(self, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Translate incoming filter requests to VectorService query format"""
        if not filters:
            return {}

        translated = {}
        supported_fields = {
            "patient_id",
            "report_id",
            "document_id",
            "document_type",
            "chunk_id",
            "chunk_index",
            "page_number",
            "section",
            "source",
            "language",
            "created_by",
            "embedding_version",
            "index_version"
        }

        for k, v in filters.items():
            if v is None:
                continue
            if k == "date":
                # date filters correspond to indexed_at timestamps range
                translated["indexed_at"] = v
            elif k == "doctor_id":
                # match creator doctor or explicit doctor identifier
                translated["doctor_id"] = v
            elif k in supported_fields:
                translated[k] = v
            else:
                translated[k] = v

        return translated

    async def retrieve_multiple(
        self,
        query: str,
        collections: List[str],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Query multiple collections simultaneously, merge and normalize scores, 
        remove duplicate chunks, and rank by score descending.
        """
        start_time = time.perf_counter()
        
        # Validation checks
        if not query or not query.strip():
            raise ValueError("Retrieval query string cannot be empty")
        if not collections:
            raise ValueError("At least one target collection must be specified")

        # 1. Generate Query Vector
        try:
            query_vector = await self.embedding_service.embed(query)
        except Exception as e:
            retrieval_metrics.record_search(0.0, success=False)
            raise RuntimeError(f"Failed to generate query vector embedding: {e}") from e

        # 2. Resolve Collections Target Names
        resolved_cols = []
        for col in collections:
            resolved_cols.append(resolve_collection_name(col))

        # 3. Translate filters
        qdrant_filters = self._translate_filters(filters)

        # 4. Search collections in parallel
        search_timeout = timeout or self.settings.TIMEOUT_SECONDS
        timeout_occurred = False

        async def search_collection(col_name: str):
            try:
                hits = await asyncio.wait_for(
                    self.vector_service.search(
                        collection_name=col_name,
                        query_vector=query_vector,
                        limit=top_k,
                        filter_dict=qdrant_filters
                    ),
                    timeout=search_timeout
                )
                return col_name, hits, False
            except asyncio.TimeoutError:
                logger.error(f"Search query timed out in collection '{col_name}' after {search_timeout}s")
                return col_name, [], True
            except Exception as e:
                logger.error(f"Search query failed in collection '{col_name}': {e}")
                raise e

        tasks = [search_collection(col) for col in resolved_cols]
        try:
            search_results = await asyncio.gather(*tasks)
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            retrieval_metrics.record_search(latency, success=False)
            raise e

        # 5. Compile and normalize raw results
        merged_matches = []
        chunks_found = 0

        for col_name, hits, timed_out in search_results:
            if timed_out:
                timeout_occurred = True
                continue

            chunks_found += len(hits)
            for hit in hits:
                raw_score = hit["score"]
                norm_score = self.normalize_score(raw_score)

                # Score threshold filter
                if score_threshold is not None and norm_score < score_threshold:
                    continue

                payload = hit["payload"] or {}
                
                # Citations composition
                citations = {
                    "document_id": payload.get("document_id"),
                    "chunk_index": payload.get("chunk_index"),
                    "page_number": payload.get("page_number", 1),
                    "section": payload.get("section", "content")
                }

                match_item = {
                    "collection": col_name,
                    "id": hit["id"],
                    "score": norm_score,
                    "content": payload.get("content", ""),
                    "metadata": payload,
                    "document_type": payload.get("document_type", "UNKNOWN"),
                    "patient_id": payload.get("patient_id"),
                    "report_id": payload.get("report_id"),
                    "citations": citations
                }
                merged_matches.append(match_item)

        # 6. Deduplicate results by content_hash
        deduplicated = {}
        for match in merged_matches:
            content_hash = match["metadata"].get("content_hash")
            if not content_hash:
                from app.utils.hash import generate_content_hash
                content_hash = generate_content_hash(match["content"])

            if content_hash in deduplicated:
                # Keep the match with the higher score
                if match["score"] > deduplicated[content_hash]["score"]:
                    deduplicated[content_hash] = match
            else:
                deduplicated[content_hash] = match

        duplicates_removed = len(merged_matches) - len(deduplicated)
        final_matches = list(deduplicated.values())

        # 7. Sort Descending & slice to top_k
        final_matches.sort(key=lambda x: x["score"], reverse=True)
        final_matches = final_matches[:top_k]

        # 8. Record Telemetry
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        avg_score = sum(m["score"] for m in final_matches) / len(final_matches) if final_matches else 0.0

        retrieval_metrics.record_search(
            latency_ms=latency_ms,
            success=True,
            hits_count=len(final_matches),
            avg_score=avg_score,
            duplicates_removed=duplicates_removed,
            timeout=timeout_occurred
        )

        return {
            "results": final_matches,
            "retrieval_time": latency_ms,
            "collections_queried": resolved_cols,
            "chunks_found": chunks_found,
            "duplicates_removed": duplicates_removed
        }

    async def retrieve(
        self,
        query: str,
        collection: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query a single target collection / document type category"""
        return await self.retrieve_collection(
            query=query,
            collection=collection,
            top_k=top_k,
            score_threshold=score_threshold,
            filters=filters
        )

    async def retrieve_collection(
        self,
        query: str,
        collection: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convenience method to retrieve from a single collection/document type"""
        return await self.retrieve_multiple(
            query=query,
            collections=[collection],
            filters=filters,
            top_k=top_k,
            score_threshold=score_threshold
        )

    async def retrieve_patient_reports(
        self,
        query: str,
        patient_id: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convenience helper to retrieve reports matching a specific patient_id"""
        merged_filters = dict(filters or {})
        merged_filters["patient_id"] = patient_id
        return await self.retrieve_multiple(
            query=query,
            collections=["REPORT"],
            filters=merged_filters,
            top_k=top_k,
            score_threshold=score_threshold
        )

    async def retrieve_medical_knowledge(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convenience helper to retrieve from medical guidelines articles"""
        return await self.retrieve_multiple(
            query=query,
            collections=["MEDICAL_ARTICLE"],
            filters=filters,
            top_k=top_k,
            score_threshold=score_threshold
        )

    async def retrieve_drug_knowledge(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convenience helper to retrieve drug interaction datasets"""
        return await self.retrieve_multiple(
            query=query,
            collections=["DRUG_DATASET"],
            filters=filters,
            top_k=top_k,
            score_threshold=score_threshold
        )

    async def retrieve_doctor_profiles(
        self,
        query: str,
        doctor_id: Optional[str] = None,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convenience helper to retrieve matching doctor credentials/specialization vectors"""
        merged_filters = dict(filters or {})
        if doctor_id:
            merged_filters["doctor_id"] = doctor_id
        return await self.retrieve_multiple(
            query=query,
            collections=["DOCTOR_PROFILE"],
            filters=merged_filters,
            top_k=top_k,
            score_threshold=score_threshold
        )

    async def retrieve_chat_memory(
        self,
        query: str,
        patient_id: Optional[str] = None,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convenience helper to retrieve semantic long-term memory embeddings"""
        merged_filters = dict(filters or {})
        if patient_id:
            merged_filters["patient_id"] = patient_id
        return await self.retrieve_multiple(
            query=query,
            collections=["CHAT_MEMORY"],
            filters=merged_filters,
            top_k=top_k,
            score_threshold=score_threshold
        )


# Singleton reference helper
_retrieval_service_instance = None


def get_retrieval_service() -> RetrievalService:
    """Retrieve singleton instance of RetrievalService"""
    global _retrieval_service_instance
    if _retrieval_service_instance is None:
        emb_svc = get_embedding_service()
        vec_svc = get_vector_service()
        _retrieval_service_instance = RetrievalService(
            embedding_service=emb_svc,
            vector_service=vec_svc,
            settings=ai_settings
        )
    return _retrieval_service_instance
