"""
Nura - Unit tests for RetrievalService
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.retrieval_service import RetrievalService, resolve_collection_name
from app.core.ai_config import AISettings
from app.utils.ai import retrieval_metrics


@pytest.fixture
def mock_embedding_service():
    service = AsyncMock()
    service.embed.return_value = [0.1, 0.2, 0.3]
    return service


@pytest.fixture
def mock_vector_service():
    service = AsyncMock()
    service.search.return_value = [
        {
            "id": "point_1",
            "score": 0.8,
            "payload": {
                "content": "Patient reports severe chest pain.",
                "content_hash": "hash_1",
                "document_id": "doc_1",
                "chunk_index": 0,
                "document_type": "REPORT",
                "patient_id": "pat_123"
            }
        }
    ]
    return service


def test_resolve_collection_name():
    assert resolve_collection_name("REPORT") == "patient_reports"
    assert resolve_collection_name("patient_reports") == "patient_reports"
    assert resolve_collection_name("MEDICAL_ARTICLE") == "medical_knowledge"
    
    with pytest.raises(ValueError):
        resolve_collection_name("NON_EXISTENT_TYPE")


def test_score_normalization():
    settings = AISettings()
    service = RetrievalService(
        embedding_service=MagicMock(),
        vector_service=MagicMock(),
        settings=settings
    )
    
    # Cosine score range is [-1, 1], normalized to [0, 1]
    assert service.normalize_score(1.0) == 1.0
    assert service.normalize_score(-1.0) == 0.0
    assert service.normalize_score(0.0) == 0.5


@pytest.mark.asyncio
async def test_retrieve_multiple_successful(mock_embedding_service, mock_vector_service):
    settings = AISettings()
    service = RetrievalService(
        embedding_service=mock_embedding_service,
        vector_service=mock_vector_service,
        settings=settings
    )
    
    # Trigger retrieval on multiple collections
    res = await service.retrieve_multiple(
        query="chest pain",
        collections=["REPORT", "MEDICAL_ARTICLE"],
        top_k=3,
        score_threshold=0.3
    )
    
    assert "results" in res
    assert len(res["results"]) == 1  # Deduplicated from 2 search tasks returning identical hit
    assert res["chunks_found"] == 2
    assert res["duplicates_removed"] == 1
    assert res["results"][0]["id"] == "point_1"
    assert res["results"][0]["score"] == service.normalize_score(0.8)
    
    # Assert embedding service was called
    mock_embedding_service.embed.assert_called_once_with("chest pain")


@pytest.mark.asyncio
async def test_retrieve_multiple_deduplication_keeps_highest_score(mock_embedding_service):
    settings = AISettings()
    vector_service = AsyncMock()
    
    # First collection task returns lower score, second returns higher score for same content_hash
    vector_service.search.side_effect = [
        [
            {
                "id": "point_1",
                "score": 0.4,
                "payload": {"content": "Duplicate content", "content_hash": "dup_hash"}
            }
        ],
        [
            {
                "id": "point_2",
                "score": 0.9,
                "payload": {"content": "Duplicate content", "content_hash": "dup_hash"}
            }
        ]
    ]
    
    service = RetrievalService(
        embedding_service=mock_embedding_service,
        vector_service=vector_service,
        settings=settings
    )
    
    res = await service.retrieve_multiple(
        query="test query",
        collections=["REPORT", "MEDICAL_ARTICLE"],
        top_k=5
    )
    
    # Should merge and keep point_2 (score 0.95 normalized)
    assert len(res["results"]) == 1
    assert res["results"][0]["id"] == "point_2"
    assert res["results"][0]["score"] == service.normalize_score(0.9)


@pytest.mark.asyncio
async def test_retrieve_multiple_score_threshold_filter(mock_embedding_service, mock_vector_service):
    settings = AISettings()
    service = RetrievalService(
        embedding_service=mock_embedding_service,
        vector_service=mock_vector_service,
        settings=settings
    )
    
    # Normalized score of 0.8 is (0.8 + 1) / 2 = 0.9
    # If threshold is 0.95, it should be filtered out
    res = await service.retrieve_multiple(
        query="test query",
        collections=["REPORT"],
        score_threshold=0.95
    )
    assert len(res["results"]) == 0
    
    # If threshold is 0.85, it should be included
    res2 = await service.retrieve_multiple(
        query="test query",
        collections=["REPORT"],
        score_threshold=0.85
    )
    assert len(res2["results"]) == 1


@pytest.mark.asyncio
async def test_retrieve_timeout_handling(mock_embedding_service):
    settings = AISettings()
    vector_service = AsyncMock()
    
    # Simulate a timeout error inside search
    async def delayed_search(*args, **kwargs):
        await asyncio.sleep(0.2)
        return []
    
    vector_service.search.side_effect = delayed_search
    
    service = RetrievalService(
        embedding_service=mock_embedding_service,
        vector_service=vector_service,
        settings=settings
    )
    
    retrieval_metrics.reset()
    
    # Trigger with 0.05 seconds timeout to force timeout exception
    res = await service.retrieve_multiple(
        query="timeout test",
        collections=["REPORT"],
        timeout=0.05
    )
    
    assert len(res["results"]) == 0
    metrics = retrieval_metrics.get_metrics()
    assert metrics["timeout_count"] == 1
