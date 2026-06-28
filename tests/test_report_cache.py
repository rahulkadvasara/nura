"""
Tests for ReportCacheService — OCR cache, embedding cache, summary cache, invalidation.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from app.services.report_cache.report_cache_service import ReportCacheService


SAMPLE_FILE_CONTENT = b"PDF binary content representing a medical report"
SAMPLE_TEXT = "Hemoglobin A1c result: 7.2% (Reference: <5.7%). Flagged: HIGH."
REPORT_ID = "rep-cache-test-001"


@pytest.fixture
def cache():
    svc = ReportCacheService(ocr_ttl=3600, embedding_ttl=3600, summary_ttl=3600)
    return svc


def test_ocr_cache_miss_returns_none(cache):
    """Fresh cache returns None for any file content."""
    result = cache.get_ocr(SAMPLE_FILE_CONTENT)
    assert result is None


def test_ocr_cache_hit_returns_result(cache):
    """After set_ocr, get_ocr returns the cached result for same content."""
    ocr_data = {"pages": 3, "raw_text": "Sample OCR output", "confidence": 0.95}
    cache.set_ocr(SAMPLE_FILE_CONTENT, ocr_data, report_id=REPORT_ID)
    result = cache.get_ocr(SAMPLE_FILE_CONTENT)
    assert result == ocr_data


def test_ocr_cache_different_content_miss(cache):
    """Different file content produces a cache miss even if one file was cached."""
    cache.set_ocr(SAMPLE_FILE_CONTENT, {"text": "report A"}, report_id="rep-A")
    different_content = b"completely different PDF binary"
    assert cache.get_ocr(different_content) is None


def test_embedding_cache_miss_returns_none(cache):
    """Fresh cache returns None for any text chunk."""
    result = cache.get_embedding(SAMPLE_TEXT)
    assert result is None


def test_embedding_cache_hit_returns_vector(cache):
    """After set_embedding, get_embedding returns the cached vector."""
    vector = [0.1, 0.2, 0.3, 0.4, 0.5]
    cache.set_embedding(SAMPLE_TEXT, vector, report_id=REPORT_ID)
    result = cache.get_embedding(SAMPLE_TEXT)
    assert result == vector


def test_summary_cache_miss_returns_none(cache):
    """Fresh cache returns None for any report/version combination."""
    result = cache.get_summary(REPORT_ID, version=1)
    assert result is None


def test_summary_cache_hit_returns_summary(cache):
    """After set_summary, get_summary returns the cached text for correct version."""
    summary_text = "Patient shows elevated HbA1c indicating pre-diabetic risk."
    cache.set_summary(REPORT_ID, summary_text, version=1)
    result = cache.get_summary(REPORT_ID, version=1)
    assert result == summary_text


def test_summary_cache_version_mismatch(cache):
    """Summary cached for version=1 is not returned for version=2 (cache miss)."""
    cache.set_summary(REPORT_ID, "v1 summary", version=1)
    result = cache.get_summary(REPORT_ID, version=2)
    assert result is None


def test_invalidate_report_clears_all_caches(cache):
    """invalidate_report clears OCR, embedding, and summary entries for that report."""
    cache.set_ocr(SAMPLE_FILE_CONTENT, {"text": "report"}, report_id=REPORT_ID)
    cache.set_embedding(SAMPLE_TEXT, [0.1, 0.2], report_id=REPORT_ID)
    cache.set_summary(REPORT_ID, "summary text", version=1)

    cache.invalidate_report(REPORT_ID)

    # All three should now be cache misses
    assert cache.get_ocr(SAMPLE_FILE_CONTENT) is None
    assert cache.get_embedding(SAMPLE_TEXT) is None
    assert cache.get_summary(REPORT_ID, version=1) is None


def test_invalidate_report_does_not_affect_other_reports(cache):
    """Invalidating one report does not clear cache for other report IDs."""
    other_content = b"other report content"
    other_text = "Other report clinical text"
    other_id = "rep-other-999"

    cache.set_ocr(other_content, {"text": "other"}, report_id=other_id)
    cache.set_embedding(other_text, [0.9, 0.8], report_id=other_id)
    cache.set_summary(other_id, "other summary", version=1)

    # Invalidate a DIFFERENT report
    cache.invalidate_report(REPORT_ID)

    # Other report's cache should still be intact
    assert cache.get_ocr(other_content) == {"text": "other"}
    assert cache.get_embedding(other_text) == [0.9, 0.8]
    assert cache.get_summary(other_id, version=1) == "other summary"


def test_get_stats_returns_sizes(cache):
    """get_stats returns accurate entry counts for each cache."""
    cache.set_ocr(SAMPLE_FILE_CONTENT, {}, report_id=REPORT_ID)
    cache.set_embedding(SAMPLE_TEXT, [0.1], report_id=REPORT_ID)
    cache.set_summary(REPORT_ID, "summary", version=1)

    stats = cache.get_stats()
    assert stats["ocr"]["size"] == 1
    assert stats["embedding"]["size"] == 1
    assert stats["summary"]["size"] == 1


def test_prune_expired_removes_stale_entries():
    """Entries with negative TTL are immediately pruned by prune_expired."""
    # TTL=-1 guarantees now - ts > -1 is always True (entries are immediately stale)
    cache = ReportCacheService(ocr_ttl=-1, embedding_ttl=-1, summary_ttl=-1)
    cache.set_ocr(SAMPLE_FILE_CONTENT, {"text": "stale"})
    cache.set_embedding(SAMPLE_TEXT, [1.0, 2.0])
    cache.set_summary(REPORT_ID, "stale summary", version=1)

    pruned = cache.prune_expired()
    assert pruned["ocr"] == 1
    assert pruned["embedding"] == 1
    assert pruned["summary"] == 1
