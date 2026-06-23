import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_appointment_service,
    get_consultation_service,
    get_notification_service,
    get_audit_log_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus, ConsultationInDB
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.schemas.appointment import AppointmentResponse, ConsultationResponse

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def doctor_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439002",
        email="doctor@example.com",
        password_hash="hashed_pw",
        full_name="Doctor Name",
        role=UserRole.DOCTOR,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def other_doctor_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439003",
        email="otherdoctor@example.com",
        password_hash="hashed_pw",
        full_name="Other Doctor",
        role=UserRole.DOCTOR,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def patient_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439001",
        email="patient@example.com",
        password_hash="hashed_pw",
        full_name="Patient Name",
        role=UserRole.PATIENT,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def doctor_profile():
    now = utc_now()
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439010",
        user_id="507f1f77bcf86cd799439002",
        specialization="Cardiology",
        qualifications=["MBBS"],
        experience_years=10,
        consultation_fee=500.0,
        bio="Cardiologist",
        languages=["English"],
        profile_status=DoctorProfileStatus.VERIFIED,
        average_rating=4.8,
        total_reviews=12,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def other_doctor_profile():
    now = utc_now()
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439011",
        user_id="507f1f77bcf86cd799439003",
        specialization="Dermatology",
        qualifications=["MBBS"],
        experience_years=5,
        consultation_fee=300.0,
        bio="Dermatologist",
        languages=["English"],
        profile_status=DoctorProfileStatus.VERIFIED,
        average_rating=4.5,
        total_reviews=2,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def sample_approved_appointment():
    now = utc_now()
    return AppointmentInDB(
        id="507f1f77bcf86cd799439050",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439010",
        availability_id="507f1f77bcf86cd799439020",
        slot_date="2026-06-25",
        slot_time="10:00",
        duration_minutes=30,
        consultation_fee=500.0,
        status=AppointmentStatus.APPROVED,
        payment_status=PaymentStatus.APPROVED,
        reason="General Consultation",
        notes=None,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def sample_in_progress_appointment():
    now = utc_now()
    return AppointmentInDB(
        id="507f1f77bcf86cd799439050",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439010",
        availability_id="507f1f77bcf86cd799439020",
        slot_date="2026-06-25",
        slot_time="10:00",
        duration_minutes=30,
        consultation_fee=500.0,
        status=AppointmentStatus.IN_PROGRESS,
        payment_status=PaymentStatus.APPROVED,
        reason="General Consultation",
        notes=None,
        consultation_started_at=now,
        created_at=now,
        updated_at=now
    )


def test_start_consultation_success(client, doctor_user, doctor_profile, sample_approved_appointment):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    from app.core.dependencies import get_doctor_profile_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    in_progress_appt = sample_approved_appointment.model_copy(update={
        "status": AppointmentStatus.IN_PROGRESS,
        "consultation_started_at": utc_now()
    })

    mock_service = AsyncMock()
    mock_service.start_consultation.return_value = in_progress_appt
    mock_service.to_response = lambda a: AppointmentResponse(
        id=a.id, patient_id=a.patient_id, doctor_id=a.doctor_id, availability_id=a.availability_id,
        slot_date=a.slot_date, slot_time=a.slot_time, duration_minutes=a.duration_minutes,
        consultation_fee=a.consultation_fee, status=a.status, payment_status=a.payment_status,
        reason=a.reason, notes=a.notes, consultation_started_at=a.consultation_started_at,
        created_at=a.created_at, updated_at=a.updated_at
    )
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    mock_audit = AsyncMock()
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit

    response = client.post("/api/v1/doctor/appointments/507f1f77bcf86cd799439050/start")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "in_progress"
    assert data["data"]["consultation_started_at"] is not None
    mock_service.start_consultation.assert_called_once_with(
        appointment_id="507f1f77bcf86cd799439050",
        doctor_profile_id=doctor_profile.id,
        doctor_user_id=doctor_user.id,
        audit_log_service=mock_audit
    )


def test_complete_consultation_success(client, doctor_user, doctor_profile, sample_in_progress_appointment):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    from app.core.dependencies import get_doctor_profile_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    consultation_record = ConsultationInDB(
        id="507f1f77bcf86cd799439090",
        appointment_id=sample_in_progress_appointment.id,
        patient_id=sample_in_progress_appointment.patient_id,
        doctor_id=doctor_profile.id,
        consultation_notes="Patient is doing well.",
        diagnosis="Common cold",
        recommendations="",
        follow_up_required=False,
        follow_up_date=None,
        created_at=utc_now(),
        updated_at=utc_now()
    )

    mock_service = AsyncMock()
    mock_service.complete_consultation.return_value = consultation_record
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    mock_consultation_service = AsyncMock()
    mock_consultation_service.to_response = lambda c: ConsultationResponse(
        id=c.id, appointment_id=c.appointment_id, patient_id=c.patient_id, doctor_id=c.doctor_id,
        consultation_notes=c.consultation_notes, diagnosis=c.diagnosis, recommendations=c.recommendations,
        follow_up_required=c.follow_up_required, follow_up_date=c.follow_up_date,
        created_at=c.created_at, updated_at=c.updated_at
    )
    app.dependency_overrides[get_consultation_service] = lambda: mock_consultation_service

    mock_notif = AsyncMock()
    app.dependency_overrides[get_notification_service] = lambda: mock_notif

    mock_audit = AsyncMock()
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit

    payload = {
        "diagnosis": "Common cold",
        "notes": "Patient is doing well.",
        "follow_up_required": False,
        "follow_up_date": None
    }

    response = client.post(
        "/api/v1/doctor/appointments/507f1f77bcf86cd799439050/complete",
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["diagnosis"] == "Common cold"
    assert data["data"]["consultation_notes"] == "Patient is doing well."


def test_start_consultation_wrong_doctor_forbidden(client, other_doctor_user, other_doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: other_doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = other_doctor_profile
    from app.core.dependencies import get_doctor_profile_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_service = AsyncMock()
    mock_service.start_consultation.side_effect = ValueError("Appointment not found or access denied")
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.post("/api/v1/doctor/appointments/507f1f77bcf86cd799439050/start")
    assert response.status_code == 400
    assert "access denied" in response.json()["message"]


def test_start_consultation_invalid_status_fails(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    from app.core.dependencies import get_doctor_profile_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_service = AsyncMock()
    mock_service.start_consultation.side_effect = ValueError("Cannot start consultation with status: pending")
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.post("/api/v1/doctor/appointments/507f1f77bcf86cd799439050/start")
    assert response.status_code == 400
    assert "Cannot start" in response.json()["message"]
