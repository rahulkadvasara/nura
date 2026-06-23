import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_appointment_service, get_notification_service, get_audit_log_service
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.schemas.appointment import AppointmentResponse

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
def sample_pending_appointment():
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
        status=AppointmentStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        reason="General Consultation",
        notes=None,
        created_at=now,
        updated_at=now
    )


def test_get_doctor_appointments_queue(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    from app.core.dependencies import get_doctor_profile_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_service = AsyncMock()
    mock_service.list_doctor_appointments.return_value = [
        {
            "id": "507f1f77bcf86cd799439050",
            "patient_id": "507f1f77bcf86cd799439001",
            "patient_name": "Patient Name",
            "appointment_date": "2026-06-25",
            "appointment_time": "10:00",
            "reason": "General Consultation",
            "status": "pending",
            "rejection_reason": None,
            "created_at": "2026-06-23T20:58:37Z"
        }
    ]
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.get("/api/v1/doctor/appointments")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["appointments"]) == 1
    assert data["data"]["appointments"][0]["patient_name"] == "Patient Name"


def test_approve_appointment_success(client, doctor_user, doctor_profile, sample_pending_appointment):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    from app.core.dependencies import get_doctor_profile_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    approved_appointment = sample_pending_appointment.model_copy(update={"status": AppointmentStatus.APPROVED})

    mock_service = AsyncMock()
    mock_service.approve_appointment.return_value = approved_appointment
    mock_service.to_response = lambda a: AppointmentResponse(
        id=a.id, patient_id=a.patient_id, doctor_id=a.doctor_id, availability_id=a.availability_id,
        slot_date=a.slot_date, slot_time=a.slot_time, duration_minutes=a.duration_minutes,
        consultation_fee=a.consultation_fee, status=a.status, payment_status=a.payment_status,
        reason=a.reason, notes=a.notes, created_at=a.created_at, updated_at=a.updated_at
    )
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    mock_notif = AsyncMock()
    app.dependency_overrides[get_notification_service] = lambda: mock_notif

    mock_audit = AsyncMock()
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit

    response = client.post("/api/v1/doctor/appointments/507f1f77bcf86cd799439050/approve")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "approved"
    mock_service.approve_appointment.assert_called_once_with(
        appointment_id="507f1f77bcf86cd799439050",
        doctor_profile_id=doctor_profile.id,
        doctor_user_id=doctor_user.id,
        notification_service=mock_notif,
        audit_log_service=mock_audit
    )


def test_reject_appointment_success(client, doctor_user, doctor_profile, sample_pending_appointment):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    from app.core.dependencies import get_doctor_profile_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    rejected_appointment = sample_pending_appointment.model_copy(update={
        "status": AppointmentStatus.REJECTED,
        "rejection_reason": "No availability"
    })

    mock_service = AsyncMock()
    mock_service.reject_appointment.return_value = rejected_appointment
    mock_service.to_response = lambda a: AppointmentResponse(
        id=a.id, patient_id=a.patient_id, doctor_id=a.doctor_id, availability_id=a.availability_id,
        slot_date=a.slot_date, slot_time=a.slot_time, duration_minutes=a.duration_minutes,
        consultation_fee=a.consultation_fee, status=a.status, payment_status=a.payment_status,
        reason=a.reason, notes=a.notes, rejection_reason=a.rejection_reason, created_at=a.created_at, updated_at=a.updated_at
    )
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    mock_notif = AsyncMock()
    app.dependency_overrides[get_notification_service] = lambda: mock_notif

    mock_audit = AsyncMock()
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit

    response = client.post(
        "/api/v1/doctor/appointments/507f1f77bcf86cd799439050/reject",
        json={"rejection_reason": "No availability"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "rejected"
    assert data["data"]["rejection_reason"] == "No availability"
    mock_service.reject_appointment.assert_called_once_with(
        appointment_id="507f1f77bcf86cd799439050",
        doctor_profile_id=doctor_profile.id,
        doctor_user_id=doctor_user.id,
        rejection_reason="No availability",
        notification_service=mock_notif,
        audit_log_service=mock_audit
    )


def test_action_by_wrong_doctor_forbidden(client, other_doctor_user, other_doctor_profile, sample_pending_appointment):
    # Other doctor tries to approve doctor_profile_id = '507f1f77bcf86cd799439010' appointment
    app.dependency_overrides[get_current_user] = lambda: other_doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = other_doctor_profile
    from app.core.dependencies import get_doctor_profile_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_service = AsyncMock()
    mock_service.approve_appointment.side_effect = ValueError("Appointment not found or access denied")
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.post("/api/v1/doctor/appointments/507f1f77bcf86cd799439050/approve")
    assert response.status_code == 400
    assert "access denied" in response.json()["message"]


def test_approve_already_approved_fails(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    from app.core.dependencies import get_doctor_profile_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_service = AsyncMock()
    mock_service.approve_appointment.side_effect = ValueError("Cannot approve appointment with status: approved")
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.post("/api/v1/doctor/appointments/507f1f77bcf86cd799439050/approve")
    assert response.status_code == 400
    assert "Cannot approve" in response.json()["message"]
