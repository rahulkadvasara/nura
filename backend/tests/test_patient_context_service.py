"""
Nura - Unit tests for PatientContextService
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from app.models.user import UserInDB, UserRole
from app.models.patient_memory import PatientMemoryInDB
from app.services.patient_context_service import PatientContextService
from app.models.appointment import AppointmentInDB, ConsultationInDB, PrescriptionInDB, Medication
from app.models.report import ReportInDB, HealthInsightInDB
from app.models.reminder import ReminderInDB


@pytest.fixture
def mock_repositories():
    return {
        "user_repository": MagicMock(),
        "patient_memory_repository": MagicMock(),
        "report_repository": MagicMock(),
        "appointment_repository": MagicMock(),
        "consultation_repository": MagicMock(),
        "prescription_repository": MagicMock(),
        "reminder_repository": MagicMock(),
        "health_insight_repository": MagicMock(),
        "chat_session_repository": MagicMock(),
    }


@pytest.mark.asyncio
async def test_assemble_context_empty_patient(mock_repositories):
    """Test that context builder behaves gracefully when patient memory or other collections are completely empty"""
    service = PatientContextService(**mock_repositories)

    # Mock user query
    user_doc = UserInDB(
        id="pt-123",
        email="patient@example.com",
        full_name="John Doe",
        role=UserRole.PATIENT,
        auth_provider="local",
        email_verified=True,
        is_active=True,
        password_hash="pass_hash"
    )
    mock_repositories["user_repository"].get = AsyncMock(return_value=user_doc)
    mock_repositories["patient_memory_repository"].get_by_patient_id = AsyncMock(return_value=None)
    mock_repositories["report_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["appointment_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["consultation_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["prescription_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["reminder_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["health_insight_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["chat_session_repository"].get_many = AsyncMock(return_value=[])

    response = await service.assemble_context("pt-123")
    
    assert response.patient_profile["id"] == "pt-123"
    assert response.patient_profile["full_name"] == "John Doe"
    assert response.medical_summary is None
    assert response.current_conditions == []
    assert response.lab_reports_summary == []
    assert response.metadata.patient_id == "pt-123"
    assert response.metadata.estimated_tokens > 0


@pytest.mark.asyncio
async def test_assemble_context_with_patient_memory(mock_repositories):
    """Test that longitudinal patient memory acts as the primary source overriding historical reconstruction"""
    service = PatientContextService(**mock_repositories)

    # Mock user query
    user_doc = UserInDB(
        id="pt-123",
        email="patient@example.com",
        full_name="John Doe",
        role=UserRole.PATIENT,
        auth_provider="local",
        email_verified=True,
        is_active=True,
        password_hash="pass_hash"
    )
    
    memory_doc = PatientMemoryInDB(
        id="pm-456",
        patient_id="pt-123",
        ai_summary="Patient is a 45-year old male with controlled diabetes.",
        chronic_conditions=["Diabetes Type 2"],
        allergies=["Penicillin"],
        medications=["Metformin 500mg"],
        surgeries=["Appendectomy"],
        diagnoses=["Hyperlipidemia"],
        health_risks=["Cardiovascular risk"],
        recent_findings=["Fasting blood glucose stable"],
        lifestyle_notes="Drinks occasionally, non-smoker",
        timeline=[{"event": "Diagnosed in 2021"}]
    )

    mock_repositories["user_repository"].get = AsyncMock(return_value=user_doc)
    mock_repositories["patient_memory_repository"].get_by_patient_id = AsyncMock(return_value=memory_doc)
    mock_repositories["report_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["appointment_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["consultation_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["prescription_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["reminder_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["health_insight_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["chat_session_repository"].get_many = AsyncMock(return_value=[])

    response = await service.assemble_context("pt-123")
    
    assert response.medical_summary == "Patient is a 45-year old male with controlled diabetes."
    assert "Diabetes Type 2" in response.current_conditions
    assert "Hyperlipidemia" in response.current_conditions
    assert response.medication_allergies == ["Penicillin"]
    assert response.current_medications == ["Metformin 500mg"]
    assert "Appendectomy" in response.past_medical_history
    assert response.lifestyle_notes == "Drinks occasionally, non-smoker"


@pytest.mark.asyncio
async def test_assemble_context_compression(mock_repositories):
    """Test that context list summaries are compressed to fit inside a low token budget"""
    service = PatientContextService(**mock_repositories)

    # Mock user query
    user_doc = UserInDB(
        id="pt-123",
        email="patient@example.com",
        full_name="John Doe",
        role=UserRole.PATIENT,
        auth_provider="local",
        email_verified=True,
        is_active=True,
        password_hash="pass_hash"
    )
    mock_repositories["user_repository"].get = AsyncMock(return_value=user_doc)
    mock_repositories["patient_memory_repository"].get_by_patient_id = AsyncMock(return_value=None)
    
    # Return 10 reports
    fake_reports = [
        ReportInDB(
            id=f"rep-{i}",
            patient_id="pt-123",
            uploaded_by="doc-123",
            report_type="blood_test",
            file_url=f"http://example.com/rep-{i}.pdf",
            raw_text=f"Raw text chunk data for report number {i} containing some details",
            ai_summary=f"Report summary number {i} detailing some issues",
            risk_level="medium",
            processing_status="completed"
        )
        for i in range(10)
    ]
    mock_repositories["report_repository"].get_many = AsyncMock(return_value=fake_reports)
    mock_repositories["appointment_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["consultation_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["prescription_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["reminder_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["health_insight_repository"].get_many = AsyncMock(return_value=[])
    mock_repositories["chat_session_repository"].get_many = AsyncMock(return_value=[])

    # Case 1: High budget -> Returns max items (up to 5 default)
    res_high = await service.assemble_context("pt-123", token_budget=1000)
    assert len(res_high.lab_reports_summary) == 5

    # Case 2: Low budget -> Compresses down list to 1 item to stay inside low budget
    res_low = await service.assemble_context("pt-123", token_budget=15)
    assert len(res_low.lab_reports_summary) == 1
