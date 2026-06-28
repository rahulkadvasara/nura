import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel
from app.services.report_pipeline.pipeline_service import PipelineService
from app.services.report_pipeline.pipeline_state import PipelineState


@pytest.mark.asyncio
async def test_pipeline_orchestrator_success():
    report_id = "rep-123"
    patient_id = "pat-123"

    report = ReportInDB(
        id=report_id,
        patient_id=patient_id,
        uploaded_by=patient_id,
        report_type=ReportType.BLOOD_TEST,
        file_url="uploads/reports/test.pdf",
        processing_status=ProcessingStatus.UPLOADED,
        risk_level=RiskLevel.LOW,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    # Mock repositories
    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(side_effect=[report, report, report, report, report, report])
    mock_repo.collection = MagicMock()
    mock_repo.collection.update_one = AsyncMock()

    # Mock stages services
    mock_ocr = MagicMock()
    mock_ocr.process_report = AsyncMock()

    mock_extraction = MagicMock()
    mock_extraction.extract_medical_information = AsyncMock()

    mock_risk = MagicMock()
    mock_risk.analyze_report_risks = AsyncMock()

    mock_summary = MagicMock()
    mock_summary.generate_report_summary = AsyncMock()

    mock_sync = MagicMock()
    mock_sync.synchronize_report = AsyncMock()

    # Mock telemetry and validation
    mock_telemetry = MagicMock()
    mock_telemetry.record_stage_duration = AsyncMock()
    mock_telemetry.record_retry = AsyncMock()

    mock_validator = MagicMock()
    mock_validator.validate_report_readiness = AsyncMock(return_value={"valid": True, "issues": []})

    # Mock dispatcher
    mock_dispatcher = MagicMock()
    mock_dispatcher.dispatch = AsyncMock()

    service = PipelineService(
        report_repository=mock_repo,
        document_parser=mock_ocr,
        extraction_service=mock_extraction,
        risk_service=mock_risk,
        understanding_service=mock_summary,
        sync_service=mock_sync,
        telemetry=mock_telemetry,
        validator=mock_validator,
        event_dispatcher=mock_dispatcher,
        max_stage_retries=2
    )

    res = await service.execute_pipeline(report_id)

    assert res["success"] is True
    assert res["status"] == PipelineState.READY

    # Assert that all stages were executed
    mock_ocr.process_report.assert_called_once_with(report_id)
    mock_extraction.extract_medical_information.assert_called_once_with(report_id)
    mock_risk.analyze_report_risks.assert_called_once_with(report_id)
    mock_summary.generate_report_summary.assert_called_once_with(report_id)
    mock_sync.synchronize_report.assert_called_once_with(report_id)
