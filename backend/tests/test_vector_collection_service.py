"""
Nura - Unit tests for VectorCollectionService
"""

import pytest
from unittest.mock import MagicMock, patch
from qdrant_client.http import models as qdrant_models
from app.services.vector_collection_service import VectorCollectionService
from app.core.exceptions import AIConfigurationError


@pytest.fixture
def mock_client():
    client = MagicMock()
    
    # Mock get_collections
    col_1 = MagicMock()
    col_1.name = "patient_reports"
    res = MagicMock()
    res.collections = [col_1]
    client.get_collections.return_value = res
    
    # Mock get_collection info
    col_info = MagicMock()
    col_info.status = "green"
    col_info.vectors_count = 120
    vectors_config = MagicMock()
    vectors_config.size = 384
    vectors_config.distance = qdrant_models.Distance.COSINE
    col_info.config.params.vectors = vectors_config
    client.get_collection.return_value = col_info
    
    return client


@pytest.mark.asyncio
async def test_get_collection_name(mock_client):
    service = VectorCollectionService(client=mock_client)
    
    assert service.get_collection_name("patient_reports") == "patient_reports"
    
    # Test with prefix
    service.settings.QDRANT_COLLECTION_PREFIX = "test_"
    assert service.get_collection_name("patient_reports") == "test_patient_reports"
    assert service.get_collection_name("test_patient_reports") == "test_patient_reports"


@pytest.mark.asyncio
async def test_create_collection_new(mock_client):
    # Mock get_collections to return empty list
    mock_client.get_collections.return_value.collections = []
    
    service = VectorCollectionService(client=mock_client)
    service.settings.QDRANT_COLLECTION_PREFIX = ""
    
    created = await service.create_collection("new_col", vector_size=384, distance="cosine")
    
    assert created is True
    mock_client.create_collection.assert_called_once()
    args, kwargs = mock_client.create_collection.call_args
    assert kwargs["collection_name"] == "new_col"
    assert kwargs["vectors_config"].size == 384
    assert kwargs["vectors_config"].distance == qdrant_models.Distance.COSINE


@pytest.mark.asyncio
async def test_create_collection_exists_valid(mock_client):
    service = VectorCollectionService(client=mock_client)
    service.settings.QDRANT_COLLECTION_PREFIX = ""
    
    # Collection 'patient_reports' already exists according to mock_client fixture
    created = await service.create_collection("patient_reports", vector_size=384, distance="cosine")
    
    assert created is False
    mock_client.create_collection.assert_not_called()


@pytest.mark.asyncio
async def test_create_collection_exists_dimension_mismatch(mock_client):
    # Change dimensions inside existing config to 512
    vectors_config = MagicMock()
    vectors_config.size = 512
    vectors_config.distance = qdrant_models.Distance.COSINE
    mock_client.get_collection.return_value.config.params.vectors = vectors_config
    
    service = VectorCollectionService(client=mock_client)
    service.settings.QDRANT_COLLECTION_PREFIX = ""
    
    with pytest.raises(AIConfigurationError) as exc_info:
        await service.create_collection("patient_reports", vector_size=384, distance="cosine")
        
    assert "mismatched dimensions" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_collection_exists_distance_mismatch(mock_client):
    # Change distance inside existing config to DOT
    vectors_config = MagicMock()
    vectors_config.size = 384
    vectors_config.distance = qdrant_models.Distance.DOT
    mock_client.get_collection.return_value.config.params.vectors = vectors_config
    
    service = VectorCollectionService(client=mock_client)
    service.settings.QDRANT_COLLECTION_PREFIX = ""
    
    with pytest.raises(AIConfigurationError) as exc_info:
        await service.create_collection("patient_reports", vector_size=384, distance="cosine")
        
    assert "mismatched distance metric" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_collection(mock_client):
    service = VectorCollectionService(client=mock_client)
    service.settings.QDRANT_COLLECTION_PREFIX = ""
    
    deleted = await service.delete_collection("patient_reports")
    assert deleted is True
    mock_client.delete_collection.assert_called_once_with(collection_name="patient_reports")
    
    # Try deleting non-existent collection
    deleted_nonexistent = await service.delete_collection("nonexistent")
    assert deleted_nonexistent is False


@pytest.mark.asyncio
async def test_get_collection_stats(mock_client):
    service = VectorCollectionService(client=mock_client)
    service.settings.QDRANT_COLLECTION_PREFIX = ""
    
    stats = await service.get_collection_stats("patient_reports")
    assert stats["name"] == "patient_reports"
    assert stats["status"] == "green"
    assert stats["vector_count"] == 120
    assert stats["dimensions"] == 384
    assert stats["distance"] == "COSINE"


@pytest.mark.asyncio
async def test_health_check_healthy(mock_client):
    service = VectorCollectionService(client=mock_client)
    health = await service.health_check()
    
    assert health["status"] == "healthy"
    assert health["connected"] is True
    assert "latency" in health


@pytest.mark.asyncio
async def test_health_check_unhealthy(mock_client):
    # Force get_collections to throw exception
    mock_client.get_collections.side_effect = Exception("Connection refused")
    
    service = VectorCollectionService(client=mock_client)
    health = await service.health_check()
    
    assert health["status"] == "unhealthy"
    assert health["connected"] is False
    assert "Connection refused" in health["error"]
