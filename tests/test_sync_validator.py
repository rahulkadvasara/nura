import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from app.services.report_sync.sync_validator import ReportSyncValidator
from app.models.report import ReportInDB, ReportType, ProcessingStatus
from app.models.patient_memory import PatientMemoryInDB


@pytest.fixture
def mock_validator_dependencies():
    return {
        "report_repository": MagicMock(),
        "patient_memory_repository": MagicMock(),
        "vector_service": MagicMock(),
        "index_version_service": MagicMock(),
        "chunk_builder": MagicMock()
    }


@pytest.mark.asyncio
async def test_validate_synchronization_success(mock_validator_dependencies):
    validator = ReportSyncValidator(**mock_validator_dependencies)

    # 1. Mock Report
    report = ReportInDB(
        id="rep-123",
        patient_id="pat-123",
        uploaded_by="pat-123",
        report_type=ReportType.BLOOD_TEST,
        file_url="http://url/pdf",
        processing_status=ProcessingStatus.COMPLETED,
        ai_summary="Sugar stable.",
        overall_risk="LOW",
        risk_score=20,
        created_at=datetime.now(timezone.utc)
    )
    mock_validator_dependencies["report_repository"].get = AsyncMock(return_value=report)

    # 2. Mock patient memory (MongoDB side)
    memory = PatientMemoryInDB(
        id="mem-123",
        patient_id="pat-123",
        ai_summary="Baseline health.",
        chronic_conditions=[],
        allergies=[],
        medications=[],
        surgeries=[],
        diagnoses=[],
        health_risks=[],
        recent_findings=[],
        timeline=[],
        latest_report_summary="Sugar stable.",
        last_updated=datetime.now(timezone.utc)
    )
    mock_validator_dependencies["patient_memory_repository"].get_by_patient_id = AsyncMock(return_value=memory)

    # 3. Mock expected chunks
    expected_chunks = [{"text": "Expected chunk 1", "section": "key_findings"}]
    mock_validator_dependencies["chunk_builder"].build_report_chunks = MagicMock(return_value=expected_chunks)

    # 4. Mock Qdrant scroll (Qdrant side)
    qdrant_points = [
        {
            "id": "pt-1",
            "payload": {
                "patient_id": "pat-123",
                "report_id": "rep-123",
                "document_type": "blood_test",
                "report_date": datetime.now(timezone.utc).isoformat(),
                "section": "key_findings",
                "embedding_version": "v1",
                "text": "Expected chunk 1"
            }
        }
    ]
    mock_validator_dependencies["vector_service"].scroll = AsyncMock(return_value=(qdrant_points, None))
    mock_validator_dependencies["index_version_service"].get_embedding_version = MagicMock(return_value="v1")

    res = await validator.validate_synchronization("rep-123")

    assert res["in_sync"] is True
    assert res["validation_details"]["mongodb_valid"] is True
    assert res["validation_details"]["qdrant_valid"] is True
    assert res["validation_details"]["version_synchronized"] is True
