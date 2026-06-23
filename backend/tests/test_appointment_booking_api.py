import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.core.dependencies import get_current_user, get_appointment_service
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus, DoctorAvailabilityInDB, DayOfWeek
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
def sample_doctor_profile():
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
def sample_appointment():
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


def test_create_appointment_success(client, patient_user, sample_appointment):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_service = AsyncMock()
    mock_service.create_appointment.return_value = sample_appointment
    
    # Mock to_response
    def fake_to_response(appt):
        return AppointmentResponse(
            id=appt.id,
            patient_id=appt.patient_id,
            doctor_id=appt.doctor_id,
            availability_id=appt.availability_id,
            slot_date=appt.slot_date,
            slot_time=appt.slot_time,
            duration_minutes=appt.duration_minutes,
            consultation_fee=appt.consultation_fee,
            status=appt.status,
            payment_status=appt.payment_status,
            reason=appt.reason,
            notes=appt.notes,
            created_at=appt.created_at,
            updated_at=appt.updated_at
        )
    mock_service.to_response = fake_to_response
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": "507f1f77bcf86cd799439010",
            "availability_slot_id": "507f1f77bcf86cd799439020",
            "reason_for_visit": "General Consultation"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "507f1f77bcf86cd799439050"
    assert data["data"]["status"] == "pending"


def test_create_appointment_validation_failure(client, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_service = AsyncMock()
    mock_service.create_appointment.side_effect = ValueError("This slot has already been booked or has a pending request")
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": "507f1f77bcf86cd799439010",
            "availability_id": "507f1f77bcf86cd799439020",
            "reason": "Double book check"
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "already been booked" in data["message"]


def test_get_my_appointments(client, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_service = AsyncMock()
    mock_service.list_patient_appointments_history.return_value = [
        {
            "id": "507f1f77bcf86cd799439050",
            "doctor_id": "507f1f77bcf86cd799439010",
            "doctor_name": "Doctor Name",
            "specialization": "Cardiology",
            "appointment_date": "2026-06-25",
            "appointment_time": "10:00",
            "status": "pending",
            "reason": "General Consultation",
            "created_at": "2026-06-23T20:58:37Z"
        }
    ]
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.get("/api/v1/appointments/my")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["appointments"]) == 1
    assert data["data"]["appointments"][0]["doctor_name"] == "Doctor Name"


def test_cancel_appointment_success(client, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_service = AsyncMock()
    mock_service.cancel_patient_appointment.return_value = AsyncMock()
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.delete("/api/v1/appointments/507f1f77bcf86cd799439050")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cancelled successfully" in data["message"]


def test_cancel_appointment_forbidden_states(client, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_service = AsyncMock()
    mock_service.cancel_patient_appointment.side_effect = ValueError("Cannot cancel appointment with status: approved")
    app.dependency_overrides[get_appointment_service] = lambda: mock_service

    response = client.delete("/api/v1/appointments/507f1f77bcf86cd799439050")
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Cannot cancel appointment" in data["message"]


def test_patient_authorization_enforced(client, doctor_user):
    # Logged in as doctor, not patient
    app.dependency_overrides[get_current_user] = lambda: doctor_user

    response = client.get("/api/v1/appointments/my")
    # Should get forbidden access because route requires UserRole.PATIENT
    assert response.status_code == 403
