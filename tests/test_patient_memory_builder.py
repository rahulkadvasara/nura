import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from app.services.report_sync.patient_memory_builder import ReportPatientMemoryBuilder
from app.models.patient_memory import PatientMemoryInDB, PatientMemoryCreate
from app.models.report import ReportInDB, ReportType, ProcessingStatus


@pytest.mark.asyncio
async def test_build_incremental_memory_first_time():
    mock_repo = MagicMock()
    mock_repo.get_by_patient_id = AsyncMock(return_value=None)

    mock_summary_builder = MagicMock()
    baseline = PatientMemoryCreate(
        patient_id="pat-123",
        ai_summary="Baseline health summary details.",
        chronic_conditions=[],
        allergies=[],
        medications=[],
        surgeries=[],
        diagnoses=[],
        health_risks=[],
        recent_findings=[],
        timeline=[]
    )
    mock_summary_builder.build_summary = AsyncMock(return_value=baseline)

    builder = ReportPatientMemoryBuilder(mock_repo, mock_summary_builder)

    # Mock report
    report = ReportInDB(
        id="rep-123",
        patient_id="pat-123",
        uploaded_by="pat-123",
        report_type=ReportType.BLOOD_TEST,
        file_url="http://url/pdf",
        processing_status=ProcessingStatus.COMPLETED,
        ai_summary="High sugar levels.",
        overall_risk="HIGH",
        risk_score=75,
        laboratory_results=[
            {"test_name": "HbA1c", "value": 7.5, "unit": "%", "status": "HIGH", "reference_range": "4.0-5.6"}
        ],
        medications=[
            {"medicine": "Metformin", "dosage": "500mg", "frequency": "Daily", "duration": "30 days", "route": "Oral"}
        ],
        diagnoses=["Diabetes Type 2"],
        created_at=datetime.now(timezone.utc)
    )

    res = await builder.build_incremental_memory("pat-123", report)
    
    assert res.latest_report_summary == "High sugar levels."
    assert res.latest_risk is not None
    assert "HIGH" in res.latest_risk and "75" in res.latest_risk
    assert len(res.laboratory_history) == 1
    assert res.laboratory_history[0]["test_name"] == "HbA1c"
    assert len(res.medication_history) == 1
    assert res.medication_history[0]["medicine"] == "Metformin"
    assert len(res.diagnosis_history) == 1
    assert res.diagnosis_history[0]["diagnosis"] == "Diabetes Type 2"
    assert len(res.timeline) == 1
    assert "rep-123" in res.timeline[0]["ref_id"]
