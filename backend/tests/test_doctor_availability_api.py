import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_doctor_profile_service,
    get_doctor_availability_service,
    require_verified_doctor,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.doctor import (
    DoctorProfileInDB,
    DoctorProfileStatus,
    DoctorAvailabilityInDB,
    DayOfWeek,
)
from app.schemas.doctor import DoctorAvailabilityResponse

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
        id="507f1f77bcf86cd799439011",
        email="patient@example.com",
        password_hash="hashed",
        full_name="Patient User",
        role=UserRole.PATIENT,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def verified_doctor_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439022",
        email="doctor@example.com",
        password_hash="hashed",
        full_name="Doctor User",
        role=UserRole.DOCTOR,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def verified_doctor_profile():
    now = utc_now()
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439033",
        user_id="507f1f77bcf86cd799439022",
        specialization="Cardiology",
        qualifications=[],
        experience_years=10,
        consultation_fee=1000.0,
        profile_status=DoctorProfileStatus.VERIFIED,
        average_rating=0.0,
        total_reviews=0,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def mock_availability_service():
    service = AsyncMock()
    app.dependency_overrides[get_doctor_availability_service] = lambda: service
    return service


def test_get_availability_success(client, mock_availability_service, verified_doctor_profile):
    # Bypass require_verified_doctor to return verified profile
    app.dependency_overrides[require_verified_doctor] = lambda: verified_doctor_profile
    
    now = utc_now()
    sample_slot = DoctorAvailabilityInDB(
        id="507f1f77bcf86cd799439055",
        doctor_id=verified_doctor_profile.id,
        date="2026-06-25",
        day_of_week=DayOfWeek.THURSDAY,
        start_time="09:00",
        end_time="10:00",
        slot_duration=30,
        is_available=True,
        active=True,
        created_at=now,
        updated_at=now
    )
    
    mock_availability_service.get_availability_by_doctor.return_value = [sample_slot]
    mock_availability_service.to_response = MagicMock(return_value=DoctorAvailabilityResponse(
        id=sample_slot.id,
        doctor_id=sample_slot.doctor_id,
        date=sample_slot.date,
        day_of_week=sample_slot.day_of_week,
        start_time=sample_slot.start_time,
        end_time=sample_slot.end_time,
        slot_duration=sample_slot.slot_duration,
        is_available=sample_slot.is_available,
        active=sample_slot.active,
        created_at=sample_slot.created_at,
        updated_at=sample_slot.updated_at
    ))
    
    response = client.get("/api/v1/doctor/availability")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["availability"]) == 1
    assert data["data"]["availability"][0]["date"] == "2026-06-25"
    assert data["data"]["availability"][0]["day_of_week"] == "thursday"


def test_create_availability_success(client, mock_availability_service, verified_doctor_profile):
    app.dependency_overrides[require_verified_doctor] = lambda: verified_doctor_profile
    
    now = utc_now()
    created_slot = DoctorAvailabilityInDB(
        id="507f1f77bcf86cd799439055",
        doctor_id=verified_doctor_profile.id,
        date="2026-06-25",
        day_of_week=DayOfWeek.THURSDAY,
        start_time="09:00",
        end_time="10:00",
        slot_duration=30,
        is_available=True,
        active=True,
        created_at=now,
        updated_at=now
    )
    
    mock_availability_service.create_availability.return_value = created_slot
    mock_availability_service.to_response = MagicMock(return_value=DoctorAvailabilityResponse(
        id=created_slot.id,
        doctor_id=created_slot.doctor_id,
        date=created_slot.date,
        day_of_week=created_slot.day_of_week,
        start_time=created_slot.start_time,
        end_time=created_slot.end_time,
        slot_duration=created_slot.slot_duration,
        is_available=created_slot.is_available,
        active=created_slot.active,
        created_at=created_slot.created_at,
        updated_at=created_slot.updated_at
    ))
    
    payload = {
        "date": "2026-06-25",
        "start_time": "09:00",
        "end_time": "10:00",
        "slot_duration": 30,
        "is_available": True
    }
    
    response = client.post("/api/v1/doctor/availability", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["date"] == "2026-06-25"
    assert data["data"]["day_of_week"] == "thursday"


def test_create_availability_overlap_error(client, mock_availability_service, verified_doctor_profile):
    app.dependency_overrides[require_verified_doctor] = lambda: verified_doctor_profile
    
    mock_availability_service.create_availability.side_effect = ValueError("Overlapping time slot exists")
    
    payload = {
        "date": "2026-06-25",
        "start_time": "09:00",
        "end_time": "10:00"
    }
    
    response = client.post("/api/v1/doctor/availability", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Overlapping" in data["message"]


def test_update_availability_locked_error(client, mock_availability_service, verified_doctor_profile):
    app.dependency_overrides[require_verified_doctor] = lambda: verified_doctor_profile
    
    # Mock search lookup of the slot to match current doctor
    existing_slot = DoctorAvailabilityInDB(
        id="507f1f77bcf86cd799439055",
        doctor_id=verified_doctor_profile.id,
        date="2026-06-25",
        day_of_week=DayOfWeek.THURSDAY,
        start_time="09:00",
        end_time="10:00",
        slot_duration=30,
        is_available=True,
        active=True
    )
    mock_availability_service.get_availability_by_id.return_value = existing_slot
    mock_availability_service.update_availability.side_effect = ValueError(
        "Cannot modify or delete this slot because there is an approved appointment scheduled for it"
    )
    
    payload = {
        "start_time": "09:30"
    }
    
    response = client.put("/api/v1/doctor/availability/507f1f77bcf86cd799439055", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "approved appointment" in data["message"]


def test_delete_availability_locked_error(client, mock_availability_service, verified_doctor_profile):
    app.dependency_overrides[require_verified_doctor] = lambda: verified_doctor_profile
    
    existing_slot = DoctorAvailabilityInDB(
        id="507f1f77bcf86cd799439055",
        doctor_id=verified_doctor_profile.id,
        date="2026-06-25",
        day_of_week=DayOfWeek.THURSDAY,
        start_time="09:00",
        end_time="10:00",
        slot_duration=30,
        is_available=True,
        active=True
    )
    mock_availability_service.get_availability_by_id.return_value = existing_slot
    mock_availability_service.delete_availability.side_effect = ValueError(
        "Cannot modify or delete this slot because there is an approved appointment scheduled for it"
    )
    
    response = client.delete("/api/v1/doctor/availability/507f1f77bcf86cd799439055")
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "approved appointment" in data["message"]


def test_availability_guard_restrictions(client, mock_availability_service, patient_user, verified_doctor_user):
    # Test 1: Patient role user calling endpoint
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    response = client.get("/api/v1/doctor/availability")
    assert response.status_code == 403
    
    # Test 2: Doctor user calling, but has no profile
    app.dependency_overrides[get_current_user] = lambda: verified_doctor_user
    
    # Mock doctor profile service to return None
    profile_svc = AsyncMock()
    profile_svc.get_profile_by_user_id.return_value = None
    app.dependency_overrides[get_doctor_profile_service] = lambda: profile_svc
    
    response = client.get("/api/v1/doctor/availability")
    assert response.status_code == 403
    
    # Test 3: Doctor user calling, profile exists but status is pending
    pending_profile = DoctorProfileInDB(
        id="507f1f77bcf86cd799439033",
        user_id=verified_doctor_user.id,
        specialization="Cardiology",
        qualifications=[],
        experience_years=10,
        consultation_fee=1000.0,
        profile_status=DoctorProfileStatus.PENDING,
        average_rating=0.0,
        total_reviews=0,
        created_at=utc_now(),
        updated_at=utc_now()
    )
    profile_svc.get_profile_by_user_id.return_value = pending_profile
    
    response = client.get("/api/v1/doctor/availability")
    assert response.status_code == 403
