import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel
from app.models.patient_memory import PatientMemoryInDB
from app.services.report_pipeline.pipeline_validator import PipelineValidator


@pytest.mark.asyncio
async def test_pipeline_validator_passes_with_complete_report():
    """
    Validates that a report with all required fields (extraction, risk, summary,
    and a matching entry in patient_memory report_summaries) passes the audit.
    Qdrant scroll is mocked to bypass the qdrant_client filter construction.
    """
    report_id = "rep-123"
    patient_id = "pat-123"

    # Report with all required pipeline output fields
    report = ReportInDB(
        id=report_id,
        patient_id=patient_id,
        uploaded_by=patient_id,
        report_type=ReportType.BLOOD_TEST,
        file_url="uploads/reports/test.pdf",
        processing_status=ProcessingStatus.COMPLETED,
        risk_level=RiskLevel.LOW,
        overall_risk="LOW",
        laboratory_results=[{"test_name": "HbA1c", "value": "6.0"}],
        ai_summary="AI Report Summary Description",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    # Memory with this report's summary already present
    memory = PatientMemoryInDB(
        id="mem-123",
        patient_id=patient_id,
        ai_summary="Baseline health memory summary",
        longitudinal_summary="Baseline health memory summary",
        report_summaries=[{"report_id": report_id, "ai_summary": "AI Report Summary Description"}],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report_repo = MagicMock()
    mock_report_repo.get = AsyncMock(return_value=report)

    mock_memory_repo = MagicMock()
    mock_memory_repo.get_by_patient_id = AsyncMock(return_value=memory)

    # Mock Qdrant client - patch the qdrant_client import inside validator
    mock_vector_service = MagicMock()
    # We need to patch the qdrant_client.http.models import inside the validator
    mock_points = [MagicMock()]
    mock_vector_service.scroll = AsyncMock(return_value=(mock_points, None))

    validator = PipelineValidator(
        report_repository=mock_report_repo,
        patient_memory_repository=mock_memory_repo,
        vector_service=mock_vector_service
    )

    # Patch the qdrant_client.http models import to avoid import errors in test env
    fake_filter = MagicMock()
    with patch("app.services.report_pipeline.pipeline_validator.rest_models", create=True) as mock_models:
        mock_models.Filter.return_value = fake_filter
        mock_models.FieldCondition.return_value = MagicMock()
        mock_models.MatchValue.return_value = MagicMock()
        
        # Directly patch the import path
        with patch.dict("sys.modules", {"qdrant_client.http": MagicMock(), "qdrant_client.http.models": MagicMock()}):
            audit = await validator.validate_report_readiness(report_id)

    assert audit["qdrant_chunks_count"] >= 0
    assert audit["patient_id"] == patient_id
    assert audit["report_status"] == ProcessingStatus.COMPLETED
    # Validate that extraction fields were found (laboratory_results present, overall_risk present, ai_summary present)
    assert "Extracted clinical parameters are missing" not in audit["issues"]
    assert "Risk analysis parameters are missing" not in audit["issues"]
    assert "AI summary descriptions are missing" not in audit["issues"]
    assert "Report summary is missing from longitudinal memory logs" not in audit["issues"]


@pytest.mark.asyncio
async def test_pipeline_validator_reports_missing_memory():
    """Tests that the validator detects missing patient memory correctly."""
    report_id = "rep-456"
    patient_id = "pat-456"

    report = ReportInDB(
        id=report_id,
        patient_id=patient_id,
        uploaded_by=patient_id,
        report_type=ReportType.BLOOD_TEST,
        file_url="uploads/reports/test.pdf",
        processing_status=ProcessingStatus.COMPLETED,
        risk_level=RiskLevel.LOW,
        overall_risk="MEDIUM",
        laboratory_results=[{"test_name": "Glucose", "value": "110"}],
        ai_summary="Summary text for test",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report_repo = MagicMock()
    mock_report_repo.get = AsyncMock(return_value=report)

    mock_memory_repo = MagicMock()
    # Simulate missing memory
    mock_memory_repo.get_by_patient_id = AsyncMock(return_value=None)

    mock_vector_service = MagicMock()
    mock_vector_service.scroll = AsyncMock(return_value=([], None))

    validator = PipelineValidator(
        report_repository=mock_report_repo,
        patient_memory_repository=mock_memory_repo,
        vector_service=mock_vector_service
    )

    with patch.dict("sys.modules", {"qdrant_client.http": MagicMock(), "qdrant_client.http.models": MagicMock()}):
        audit = await validator.validate_report_readiness(report_id)

    assert "Longitudinal patient memory document is missing in MongoDB" in audit["issues"]
    assert audit["valid"] is False
