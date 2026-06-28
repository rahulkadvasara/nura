import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from app.services.report_sync.report_sync_service import ReportSyncService
from app.models.report import ReportInDB, ReportType, ProcessingStatus
from app.models.patient_memory import PatientMemoryCreate, PatientMemoryInDB
from app.schemas.embedding import EmbeddingResult, EmbeddingMetadata


@pytest.fixture
def mock_sync_dependencies():
    return {
        "report_repository": MagicMock(),
        "patient_memory_repository": MagicMock(),
        "memory_builder": MagicMock(),
        "chunk_builder": MagicMock(),
        "embedding_service": MagicMock(),
        "vector_service": MagicMock(),
        "index_version_service": MagicMock(),
        "audit_log_service": MagicMock()
    }


@pytest.mark.asyncio
async def test_synchronize_report_success(mock_sync_dependencies):
    service = ReportSyncService(**mock_sync_dependencies)

    # 1. Mock Report
    report = ReportInDB(
        id="rep-123",
        patient_id="pat-123",
        uploaded_by="pat-123",
        report_type=ReportType.BLOOD_TEST,
        file_url="http://url/pdf",
        processing_status=ProcessingStatus.COMPLETED,
        ai_summary="Sugar high.",
        overall_risk="HIGH",
        risk_score=75,
        created_at=datetime.now(timezone.utc)
    )
    mock_sync_dependencies["report_repository"].get = AsyncMock(return_value=report)
    mock_sync_dependencies["report_repository"].collection = MagicMock()
    mock_sync_dependencies["report_repository"].collection.update_one = AsyncMock()
    mock_sync_dependencies["report_repository"].collection.find_one = MagicMock(return_value={"_id": "rep-123"})

    # 2. Mock patient memory
    baseline = PatientMemoryCreate(
        patient_id="pat-123",
        ai_summary="Baseline summary.",
        chronic_conditions=[],
        allergies=[],
        medications=[],
        surgeries=[],
        diagnoses=[],
        health_risks=[],
        recent_findings=[],
        timeline=[]
    )
    mock_sync_dependencies["memory_builder"].build_incremental_memory = AsyncMock(return_value=baseline)
    mock_sync_dependencies["patient_memory_repository"].get_by_patient_id = AsyncMock(return_value=None)
    mock_sync_dependencies["patient_memory_repository"].create = AsyncMock()

    # 3. Mock chunks builder
    chunks = [
        {"text": "Sugar high findings details.", "section": "key_findings"}
    ]
    mock_sync_dependencies["chunk_builder"].build_report_chunks = MagicMock(return_value=chunks)

    # 4. Mock Qdrant states
    mock_sync_dependencies["vector_service"].scroll = AsyncMock(return_value=([], None))
    mock_sync_dependencies["vector_service"].delete_by_filter = AsyncMock()
    mock_sync_dependencies["vector_service"].upsert_batch = AsyncMock()

    # 5. Mock active versions
    mock_sync_dependencies["index_version_service"].get_embedding_version = MagicMock(return_value="v1")

    # 6. Mock embedding result
    dummy_emb = EmbeddingResult(
        vector=[0.1] * 384,
        text="Sugar high findings details.",
        metadata=EmbeddingMetadata(
            content_hash="hash",
            embedding_model="model",
            embedding_version="v1",
            indexed_at=datetime.now(timezone.utc),
            document_type="patient_reports",
            source_id="rep-123",
            collection_target="patient_reports"
        )
    )
    mock_sync_dependencies["embedding_service"].embed_batch = AsyncMock(return_value=[dummy_emb])
    mock_sync_dependencies["audit_log_service"].create_log = AsyncMock()

    # Run Sync
    res = await service.synchronize_report("rep-123")

    assert res["success"] is True
    assert res["chunks_count"] == 1
    assert res["upserted_count"] == 1
    mock_sync_dependencies["patient_memory_repository"].create.assert_called_once()
    mock_sync_dependencies["vector_service"].upsert_batch.assert_called_once()
