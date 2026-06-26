"""
Nura - Unit tests for DocumentIndexingService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.document_indexing_service import DocumentIndexingService
from app.core.ai_config import AISettings


@pytest.fixture
def mock_embedding_service():
    service = AsyncMock()
    service.embed.return_value = [0.1, 0.2, 0.3]
    return service


@pytest.fixture
def mock_vector_service():
    service = AsyncMock()
    service.count.return_value = 0
    service.upsert_batch.return_value = {"success": True, "errors": []}
    service.delete_by_filter.return_value = True
    return service


@pytest.fixture
def mock_metadata_service():
    service = MagicMock()
    service.build_metadata.return_value = {
        "document_id": "doc_123",
        "document_type": "REPORT",
        "chunk_id": "doc_123_chunk_0",
        "chunk_index": 0,
        "content_hash": "dummy_hash",
        "embedding_version": "v1",
        "index_version": 3
    }
    return service


@pytest.fixture
def mock_version_service():
    service = MagicMock()
    service.get_embedding_version.return_value = "v1"
    service.get_index_version.return_value = 3
    service.get_schema_version.return_value = 2
    return service


@pytest.mark.asyncio
async def test_validate_document_validation():
    settings = AISettings()
    service = DocumentIndexingService(
        embedding_service=MagicMock(),
        vector_service=MagicMock(),
        metadata_service=MagicMock(),
        version_service=MagicMock(),
        settings=settings
    )

    # Missing doc_id
    with pytest.raises(ValueError, match="Missing required parameter: document_id"):
        service.validate_document({"document_type": "REPORT", "content": "hello"})

    # Missing doc_type
    with pytest.raises(ValueError, match="Missing required parameter: document_type"):
        service.validate_document({"document_id": "doc_1", "content": "hello"})

    # Empty content
    with pytest.raises(ValueError, match="Document content cannot be empty"):
        service.validate_document({"document_id": "doc_1", "document_type": "REPORT", "content": "  "})


@pytest.mark.asyncio
async def test_index_document_successful(
    mock_embedding_service,
    mock_vector_service,
    mock_metadata_service,
    mock_version_service
):
    settings = AISettings()
    service = DocumentIndexingService(
        embedding_service=mock_embedding_service,
        vector_service=mock_vector_service,
        metadata_service=mock_metadata_service,
        version_service=mock_version_service,
        settings=settings
    )

    payload = {
        "document_id": "doc_123",
        "document_type": "REPORT",
        "content": "This is a simple test document for indexing pipeline logic.",
        "chunking_strategy": "fixed",
        "chunk_size": 20,
        "overlap": 5
    }

    res = await service.index_document(payload)

    assert res["success"] is True
    assert res["status"] == "indexed"
    assert res["document_id"] == "doc_123"
    assert res["chunks_count"] > 0
    mock_vector_service.upsert_batch.assert_called_once()


@pytest.mark.asyncio
async def test_index_document_skipped_duplicate(
    mock_embedding_service,
    mock_vector_service,
    mock_metadata_service,
    mock_version_service
):
    settings = AISettings()
    # Mock duplicate search check to say vector exists
    mock_vector_service.count.return_value = 1

    service = DocumentIndexingService(
        embedding_service=mock_embedding_service,
        vector_service=mock_vector_service,
        metadata_service=mock_metadata_service,
        version_service=mock_version_service,
        settings=settings
    )

    payload = {
        "document_id": "doc_123",
        "document_type": "REPORT",
        "content": "Simple text",
        "chunking_strategy": "fixed",
        "chunk_size": 100,
        "overlap": 0
    }

    res = await service.index_document(payload)

    assert res["success"] is True
    assert res["status"] == "skipped"
    assert res["chunks_count"] == 0
    assert res["skipped_count"] == 1
    # Should not call upsert
    mock_vector_service.upsert_batch.assert_not_called()


@pytest.mark.asyncio
async def test_index_documents_batch(
    mock_embedding_service,
    mock_vector_service,
    mock_metadata_service,
    mock_version_service
):
    settings = AISettings()
    service = DocumentIndexingService(
        embedding_service=mock_embedding_service,
        vector_service=mock_vector_service,
        metadata_service=mock_metadata_service,
        version_service=mock_version_service,
        settings=settings
    )

    docs = [
        {
            "document_id": "doc_a",
            "document_type": "REPORT",
            "content": "Valid report content details."
        },
        {
            "document_id": "doc_b",
            "document_type": "REPORT",
            "content": "Another valid reports text content."
        }
    ]

    results = await service.index_documents(docs)

    assert len(results) == 2
    assert results[0]["success"] is True
    assert results[0]["document_id"] == "doc_a"
    assert results[1]["success"] is True
    assert results[1]["document_id"] == "doc_b"


@pytest.mark.asyncio
async def test_reindex_document(
    mock_embedding_service,
    mock_vector_service,
    mock_metadata_service,
    mock_version_service
):
    settings = AISettings()
    service = DocumentIndexingService(
        embedding_service=mock_embedding_service,
        vector_service=mock_vector_service,
        metadata_service=mock_metadata_service,
        version_service=mock_version_service,
        settings=settings
    )

    payload = {
        "document_id": "doc_123",
        "document_type": "REPORT",
        "content": "Reindexed content string."
    }

    res = await service.reindex_document(payload)

    assert res["success"] is True
    assert res["status"] == "indexed"
    # Verify deletion was called before insertion
    mock_vector_service.delete_by_filter.assert_called_once_with(
        "patient_reports", {"document_id": "doc_123"}
    )
    mock_vector_service.upsert_batch.assert_called_once()
