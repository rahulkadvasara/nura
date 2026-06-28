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
async def test_pipeline_partial_recovery_skips_ocr():
    report_id = "rep-123"
    patient_id = "pat-123"

    # Report has ocr_status as completed
    report = ReportInDB(
        id=report_id,
        patient_id=patient_id,
        uploaded_by=patient_id,
        report_type=ReportType.BLOOD_TEST,
        file_url="uploads/reports/test.pdf",
        processing_status=ProcessingStatus.PROCESSING,
        ocr_status="completed",
        extraction_status="pending",
        risk_level=RiskLevel.LOW,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(side_effect=[report, report, report, report, report, report])
    mock_repo.collection = MagicMock()
    mock_repo.collection.update_one = AsyncMock()

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

    mock_telemetry = MagicMock()
    mock_telemetry.record_stage_duration = AsyncMock()
    mock_telemetry.record_retry = AsyncMock()

    mock_validator = MagicMock()
    mock_validator.validate_report_readiness = AsyncMock(return_value={"valid": True, "issues": []})

    service = PipelineService(
        report_repository=mock_repo,
        document_parser=mock_ocr,
        extraction_service=mock_extraction,
        risk_service=mock_risk,
        understanding_service=mock_summary,
        sync_service=mock_sync,
        telemetry=mock_telemetry,
        validator=mock_validator,
        event_dispatcher=None,
        max_stage_retries=2
    )

    res = await service.execute_pipeline(report_id)

    assert res["success"] is True
    assert res["status"] == PipelineState.READY

    # Assert OCR was SKIPPED
    mock_ocr.process_report.assert_not_called()
    
    # Assert other stages ran
    mock_extraction.extract_medical_information.assert_called_once_with(report_id)
    mock_risk.analyze_report_risks.assert_called_once_with(report_id)


@pytest.mark.asyncio
async def test_pipeline_stage_retry_limit():
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

    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(return_value=report)
    mock_repo.collection = MagicMock()
    mock_repo.collection.update_one = AsyncMock()

    # OCR fails consistently
    mock_ocr = MagicMock()
    mock_ocr.process_report = AsyncMock(side_effect=RuntimeError("OCR Hardware Timeout"))

    mock_extraction = MagicMock()
    mock_risk = MagicMock()
    mock_summary = MagicMock()
    mock_sync = MagicMock()

    mock_telemetry = MagicMock()
    mock_telemetry.record_stage_duration = AsyncMock()
    mock_telemetry.record_retry = AsyncMock()

    mock_validator = MagicMock()

    service = PipelineService(
        report_repository=mock_repo,
        document_parser=mock_ocr,
        extraction_service=mock_extraction,
        risk_service=mock_risk,
        understanding_service=mock_summary,
        sync_service=mock_sync,
        telemetry=mock_telemetry,
        validator=mock_validator,
        event_dispatcher=None,
        max_stage_retries=3
    )

    res = await service.execute_pipeline(report_id)

    assert res["success"] is False
    assert res["status"] == PipelineState.FAILED
    assert "OCR Processing stage failed" in res["error"]

    # Assert ocr called 3 times (retried twice after initial attempt)
    assert mock_ocr.process_report.call_count == 3
    assert mock_telemetry.record_retry.call_count == 3
