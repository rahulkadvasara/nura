"""
Nura - Unit tests for RAGCacheService
"""
import pytest
import time
from unittest.mock import MagicMock
from app.services.rag_cache_service import RAGCacheService, serialize_key_params
from app.core.ai_config import AISettings
from app.utils.ai import rag_cache_metrics

@pytest.fixture
def clean_metrics():
    rag_cache_metrics.reset()
    yield rag_cache_metrics
    rag_cache_metrics.reset()

def test_serialize_key_params():
    key1 = serialize_key_params("What is diabetes?", ["patient_reports", "medical_knowledge"], {"patient_id": "p123"}, top_k=5)
    key2 = serialize_key_params(" what is diabetes? ", ["medical_knowledge", "patient_reports"], {"patient_id": "p123"}, top_k=5)
    assert key1 == key2

def test_query_cache(clean_metrics):
    settings = AISettings()
    settings.QUERY_CACHE_TTL = 10
    cache = RAGCacheService(settings=settings)

    # Miss check
    assert cache.get_query("diabetes") is None
    assert clean_metrics.get_metrics()["query_misses"] == 1

    # Set and Hit check
    cache.set_query("diabetes", "medical_question", {"medical_question": 0.9})
    res = cache.get_query("diabetes")
    assert res is not None
    assert res[0] == "medical_question"
    assert clean_metrics.get_metrics()["query_hits"] == 1

def test_embedding_cache(clean_metrics):
    settings = AISettings()
    settings.EMBEDDING_CACHE_TTL = 10
    cache = RAGCacheService(settings=settings)

    assert cache.get_embedding("hello") is None
    assert clean_metrics.get_metrics()["embedding_misses"] == 1

    vector = [0.1, 0.2, 0.3]
    cache.set_embedding("hello", vector)
    assert cache.get_embedding("hello") == vector
    assert clean_metrics.get_metrics()["embedding_hits"] == 1

def test_retrieval_cache(clean_metrics):
    settings = AISettings()
    settings.RETRIEVAL_CACHE_TTL = 10
    cache = RAGCacheService(settings=settings)

    cols = ["patient_reports"]
    assert cache.get_retrieval("pain", cols) is None
    assert clean_metrics.get_metrics()["retrieval_misses"] == 1

    hits = [{"id": "doc1", "score": 0.85, "payload": {"content": "pain"}}]
    cache.set_retrieval("pain", cols, None, 5, 0.3, hits)
    assert cache.get_retrieval("pain", cols, None, 5, 0.3) == hits
    assert clean_metrics.get_metrics()["retrieval_hits"] == 1

def test_context_cache(clean_metrics):
    settings = AISettings()
    settings.CONTEXT_CACHE_TTL = 10
    cache = RAGCacheService(settings=settings)

    cols = ["patient_reports"]
    assert cache.get_context("pat123", "pain", 4000, cols) is None
    assert clean_metrics.get_metrics()["context_misses"] == 1

    ctx = {"sections": {"medical": "summarized info"}, "estimated_tokens": 120}
    cache.set_context("pat123", "pain", 4000, cols, None, ctx)
    assert cache.get_context("pat123", "pain", 4000, cols) == ctx
    assert clean_metrics.get_metrics()["context_hits"] == 1

def test_prune_expired():
    settings = AISettings()
    settings.QUERY_CACHE_TTL = 0.1
    settings.EMBEDDING_CACHE_TTL = 0.1
    settings.RETRIEVAL_CACHE_TTL = 0.1
    settings.CONTEXT_CACHE_TTL = 0.1

    cache = RAGCacheService(settings=settings)
    cache.set_query("test", "intent", {})
    cache.set_embedding("test", [1.0])
    cache.set_retrieval("test", ["col1"], None, 5, None, [])
    cache.set_context("pat", "test", 4000, ["col1"], None, {})

    # Pruning immediately shouldn't delete because time hasn't passed
    cache.prune_expired()
    assert len(cache._query_cache) == 1

    # Sleep past TTL
    time.sleep(0.15)
    cache.prune_expired()
    assert len(cache._query_cache) == 0
    assert len(cache._embedding_cache) == 0
    assert len(cache._retrieval_cache) == 0
    assert len(cache._context_cache) == 0
