"""
Nura - Unit tests for PatientSummaryBuilder
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone

from app.models.user import UserInDB, UserRole
from app.models.report import ReportInDB, HealthInsightInDB
from app.models.appointment import ConsultationInDB, PrescriptionInDB, Medication, AppointmentInDB
from app.services.patient_summary_builder import PatientSummaryBuilder


@pytest.fixture
def mock_repos():
    return {
        "user_repository": MagicMock(),
        "report_repository": MagicMock(),
        "consultation_repository": MagicMock(),
        "prescription_repository": MagicMock(),
        "health_insight_repository": MagicMock(),
        "appointment_repository": MagicMock()
    }


@pytest.mark.asyncio
async def test_patient_summary_builder_aggregation(mock_repos):
    """Test that all healthcare elements are aggregated and structured correctly"""
    builder = PatientSummaryBuilder(**mock_repos)

    patient_id = "pat-888"

    # 1. Mock User collection query (raw dict return to test dynamic profile parsing)
    mock_repos["user_repository"].collection.find_one = AsyncMock(return_value={
        "_id": patient_id,
        "full_name": "Alice Green",
        "role": "patient",
        "allergies": "Sulfa drugs, Peanuts",
        "surgeries": "Gallbladder removal",
        "lifestyle_notes": "Exercises regularly, non-smoker"
    })

    # 2. Mock Reports
    reports = [
        ReportInDB(
            id="rep-1",
            patient_id=patient_id,
            uploaded_by="doc-1",
            report_type="blood_test",
            file_url="http://url.com/1",
            raw_text="Amnesia report",
            ai_summary="Vitamin D deficient",
            processing_status="completed",
            created_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            structured_data={"conditions": ["Vitamin D Deficiency"]}
        ),
        ReportInDB(
            id="rep-2",
            patient_id=patient_id,
            uploaded_by="doc-1",
            report_type="discharge_summary",
            file_url="http://url.com/2",
            raw_text="Patient has mild hypertension",
            ai_summary="Mild Hypertension noted",
            processing_status="completed",
            created_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
            entities=[{"type": "diagnosis", "value": "Hypertension"}]
        )
    ]
    mock_repos["report_repository"].get_many = AsyncMock(return_value=reports)

    # 3. Mock Consultations
    consultations = [
        ConsultationInDB(
            id="cons-1",
            appointment_id="appt-1",
            patient_id=patient_id,
            doctor_id="doc-1",
            consultation_notes="Patient reporting knee pain",
            diagnosis="Osteoarthritis, Vitamin D Deficiency",
            created_at=datetime(2026, 6, 5, tzinfo=timezone.utc)
        )
    ]
    mock_repos["consultation_repository"].get_many = AsyncMock(return_value=consultations)

    # 4. Mock Prescriptions
    prescriptions = [
        PrescriptionInDB(
            id="pres-1",
            consultation_id="cons-1",
            patient_id=patient_id,
            doctor_id="doc-1",
            medications=[
                Medication(drug_name="Ibuprofen", dosage="400mg", frequency="Daily", duration="5 days"),
                Medication(drug_name="Vitamin D3", dosage="1000 IU", frequency="Weekly", duration="1 month")
            ],
            created_at=datetime(2026, 6, 5, tzinfo=timezone.utc)
        )
    ]
    mock_repos["prescription_repository"].get_many = AsyncMock(return_value=prescriptions)

    # 5. Mock Health Insights
    insights = [
        HealthInsightInDB(
            id="ins-1",
            patient_id=patient_id,
            insight_type="anomaly",
            title="Elevated BP",
            description="Blood pressure readings fluctuate",
            severity="high",
            created_at=datetime(2026, 6, 12, tzinfo=timezone.utc)
        )
    ]
    mock_repos["health_insight_repository"].get_many = AsyncMock(return_value=insights)

    # 6. Execute summary builder
    summary = await builder.build_summary(patient_id)

    # 7. Validations
    assert summary.patient_id == patient_id
    assert summary.lifestyle_notes == "Exercises regularly, non-smoker"
    
    # Allergies splitting
    assert "Sulfa Drugs" in summary.allergies or "Sulfa drugs" in summary.allergies
    assert "Peanuts" in summary.allergies
    
    # Surgeries
    assert "Gallbladder removal" in summary.surgeries

    # Diagnoses from consultations
    assert "Osteoarthritis" in summary.diagnoses
    assert "Vitamin D Deficiency" in summary.diagnoses

    # Chronic conditions union (Osteoarthritis, Vitamin D Deficiency, Hypertension)
    # Normed case title checking
    assert "Osteoarthritis" in summary.chronic_conditions
    assert "Vitamin D Deficiency" in summary.chronic_conditions
    assert "Hypertension" in summary.chronic_conditions

    # Medications
    assert "Ibuprofen 400mg" in summary.medications
    assert "Vitamin D3 1000 IU" in summary.medications

    # Health risks
    assert "Elevated BP: Blood pressure readings fluctuate" in summary.health_risks

    # Recent findings
    assert "Mild Hypertension noted" in summary.recent_findings
    assert "Vitamin D deficient" in summary.recent_findings

    # Timeline verification
    assert len(summary.timeline) > 0
    # Ensure items are ordered by timestamp descending (youngest first)
    timestamps = [item.get("timestamp") for item in summary.timeline if item.get("timestamp")]
    assert timestamps == sorted(timestamps, reverse=True)
