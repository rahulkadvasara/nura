"""
Nura - Unit tests for VectorService
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from qdrant_client.http import models as qdrant_models
from app.services.vector_service import VectorService
from app.core.exceptions import AIConfigurationError


@pytest.fixture
def mock_qdrant_client():
    client = MagicMock()
    
    # Mock search response
    match = MagicMock()
    match.id = "point-123"
    match.score = 0.95
    match.payload = {"source_id": "doc-abc", "patient_id": "pat-456"}
    client.search.return_value = [match]
    
    # Mock retrieve response
    point_detail = MagicMock()
    point_detail.id = "point-123"
    point_detail.payload = {"source_id": "doc-abc"}
    point_detail.vector = [0.1, 0.2]
    client.retrieve.return_value = [point_detail]
    
    # Mock count response
    count_res = MagicMock()
    count_res.count = 42
    client.count.return_value = count_res
    
    # Mock scroll response
    scroll_res = MagicMock()
    scroll_res.id = "point-789"
    scroll_res.payload = {"source_id": "doc-xyz"}
    scroll_res.vector = [0.3, 0.4]
    client.scroll.return_value = ([scroll_res], "next-token")
    
    return client


@pytest.fixture
def mock_collection_service():
    service = MagicMock()
    service.get_collection_name.side_effect = lambda x: f"nura_{x}"
    return service


def test_build_qdrant_filter():
    service = VectorService(client=MagicMock(), collection_service=MagicMock())
    
    # 1. Test empty filter dict
    assert service.build_qdrant_filter(None) is None
    assert service.build_qdrant_filter({}) is None
    
    # 2. Test standard equality filter
    f = service.build_qdrant_filter({"patient_id": "pat-123"})
    assert isinstance(f, qdrant_models.Filter)
    assert len(f.must) == 1
    assert f.must[0].key == "patient_id"
    assert f.must[0].match.value == "pat-123"
    
    # 3. Test list filter ($in / list representation)
    f = service.build_qdrant_filter({"document_type": ["report", "chat"]})
    assert len(f.must) == 1
    assert f.must[0].key == "document_type"
    assert f.must[0].match.any == ["report", "chat"]
    
    # 4. Test operators: $eq, $contains, $in
    f = service.build_qdrant_filter({
        "source_id": {"$eq": "doc-abc"},
        "tags": {"$contains": "critical"},
        "collection": {"$in": ["col1", "col2"]}
    })
    assert len(f.must) == 3
    keys = {c.key for c in f.must}
    assert keys == {"source_id", "tags", "collection"}
    
    # 5. Test range operator
    f = service.build_qdrant_filter({
        "indexed_at": {"$gte": "2026-01-01", "$lte": "2026-06-01"}
    })
    assert len(f.must) == 1
    assert f.must[0].key == "indexed_at"
    assert f.must[0].range.gte == 1767225600.0
    assert f.must[0].range.lte == 1780272000.0


@pytest.mark.asyncio
async def test_single_upsert(mock_qdrant_client, mock_collection_service):
    service = VectorService(client=mock_qdrant_client, collection_service=mock_collection_service)
    
    success = await service.upsert(
        collection_name="patient_reports",
        id="pt-123",
        vector=[0.1, 0.2, 0.3],
        payload={"source_id": "src-abc"}
    )
    
    assert success is True
    mock_qdrant_client.upsert.assert_called_once()
    args, kwargs = mock_qdrant_client.upsert.call_args
    assert kwargs["collection_name"] == "nura_patient_reports"
    assert len(kwargs["points"]) == 1
    assert kwargs["points"][0].id == "pt-123"
    assert kwargs["points"][0].vector == [0.1, 0.2, 0.3]
    assert kwargs["points"][0].payload == {"source_id": "src-abc"}


@pytest.mark.asyncio
async def test_upsert_batch_success(mock_qdrant_client, mock_collection_service):
    service = VectorService(client=mock_qdrant_client, collection_service=mock_collection_service)
    service.settings.EMBEDDING_BATCH_SIZE = 2
    
    points = [
        {"id": "id-1", "vector": [0.1], "payload": {"k": "v1"}},
        {"id": "id-2", "vector": [0.2], "payload": {"k": "v2"}},
        {"id": "id-3", "vector": [0.3], "payload": {"k": "v3"}},
    ]
    
    summary = await service.upsert_batch("patient_reports", points)
    
    assert summary["success"] is True
    assert summary["processed_count"] == 3
    assert summary["failed_count"] == 0
    assert summary["success_ids"] == ["id-1", "id-2", "id-3"]
    # Verify client was called twice because batch size is 2 (chunk 1: id-1/id-2, chunk 2: id-3)
    assert mock_qdrant_client.upsert.call_count == 2


@pytest.mark.asyncio
async def test_upsert_batch_retries_and_partial_failure(mock_qdrant_client, mock_collection_service):
    # Make upsert fail on every call
    mock_qdrant_client.upsert.side_effect = Exception("Write timeout")
    
    service = VectorService(client=mock_qdrant_client, collection_service=mock_collection_service)
    service.settings.EMBEDDING_BATCH_SIZE = 5
    
    points = [
        {"id": "id-1", "vector": [0.1], "payload": {"k": "v"}},
        {"id": "id-2", "vector": [0.2], "payload": {"k": "v"}},
    ]
    
    # Patch asyncio.sleep to run instantly during test
    with patch("asyncio.sleep", return_value=None) as mock_sleep:
        summary = await service.upsert_batch("patient_reports", points)
        
        assert summary["success"] is False
        assert summary["processed_count"] == 0
        assert summary["failed_count"] == 2
        assert summary["failed_ids"] == ["id-1", "id-2"]
        assert len(summary["errors"]) == 1
        
        # Verify 3 retries were executed
        assert mock_qdrant_client.upsert.call_count == 3
        assert mock_sleep.call_count == 2  # first retry wait, second retry wait


@pytest.mark.asyncio
async def test_search_matches(mock_qdrant_client, mock_collection_service):
    service = VectorService(client=mock_qdrant_client, collection_service=mock_collection_service)
    
    results = await service.search(
        collection_name="patient_reports",
        query_vector=[0.1, 0.2],
        limit=5,
        filter_dict={"patient_id": "pat-456"}
    )
    
    assert len(results) == 1
    assert results[0]["id"] == "point-123"
    assert results[0]["score"] == 0.95
    assert results[0]["payload"]["source_id"] == "doc-abc"
    mock_qdrant_client.search.assert_called_once()


@pytest.mark.asyncio
async def test_delete_by_ids(mock_qdrant_client, mock_collection_service):
    service = VectorService(client=mock_qdrant_client, collection_service=mock_collection_service)
    
    success = await service.delete("patient_reports", ["id-1", "id-2"])
    
    assert success is True
    mock_qdrant_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_scroll_results(mock_qdrant_client, mock_collection_service):
    service = VectorService(client=mock_qdrant_client, collection_service=mock_collection_service)
    
    points, token = await service.scroll("patient_reports", limit=1, offset="start")
    
    assert len(points) == 1
    assert points[0]["id"] == "point-789"
    assert token == "next-token"
    mock_qdrant_client.scroll.assert_called_once()
