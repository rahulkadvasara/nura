"""
Nura - Unit tests for DocumentMetadataService
"""
import pytest
from app.services.document_metadata_service import DocumentMetadataService
from app.services.index_version_service import IndexVersionService
from app.core.ai_config import AISettings


def test_build_metadata_fields():
    settings = AISettings()
    settings.EMBEDDING_MODEL = "test-model"
    settings.EMBEDDING_VERSION = "v1"
    settings.INDEX_VERSION = 3

    version_service = IndexVersionService(settings=settings)
    metadata_service = DocumentMetadataService(version_service=version_service, settings=settings)

    metadata = metadata_service.build_metadata(
        document_id="doc_123",
        document_type="REPORT",
        chunk_index=0,
        content="Test content block",
        patient_id="pat_456",
        report_id="rep_789",
        page_number=2,
        section="diagnosis",
        source="unit_test",
        language="en",
        created_by="tester"
    )

    # Verify all 16 standardized metadata fields
    assert metadata["patient_id"] == "pat_456"
    assert metadata["report_id"] == "rep_789"
    assert metadata["document_id"] == "doc_123"
    assert metadata["document_type"] == "REPORT"
    assert metadata["chunk_id"] == "doc_123_chunk_0"
    assert metadata["chunk_index"] == 0
    assert metadata["page_number"] == 2
    assert metadata["section"] == "diagnosis"
    assert metadata["source"] == "unit_test"
    assert metadata["language"] == "en"
    assert metadata["created_by"] == "tester"
    assert "indexed_at" in metadata
    assert metadata["embedding_model"] == "test-model"
    assert metadata["embedding_version"] == "v1"
    assert "content_hash" in metadata
    assert metadata["index_version"] == 3

    # Verify content hash matches a valid SHA-256 string
    assert len(metadata["content_hash"]) == 64
