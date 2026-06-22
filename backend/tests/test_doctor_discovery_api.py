import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_doctor_profile_service,
    get_doctor_availability_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.doctor import (
    DoctorProfileStatus,
    DoctorAvailabilityInDB,
    DayOfWeek,
)
from app.schemas.doctor import DoctorDiscoveryResponse, DoctorAvailabilityResponse

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
def mock_discovery_doctor():
    return DoctorDiscoveryResponse(
        id="507f1f77bcf86cd799439033",
        user_id="507f1f77bcf86cd799439022",
        name="Dr. Verified John",
        specialization="Cardiology",
        qualifications=["MBBS", "MD"],
        experience_years=12,
        consultation_fee=1000.0,
        bio="Cardiology specialist",
        languages=["English", "Hindi"],
        hospital="City Hospital",
        education="AIIMS",
        profile_picture="https://example.com/john.jpg",
        average_rating=4.5,
        total_reviews=20
    )

@pytest.fixture
def mock_availability_slot():
    now = utc_now()
    return DoctorAvailabilityInDB(
        id="507f1f77bcf86cd799439044",
        doctor_id="507f1f77bcf86cd799439033",
        date=(datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), # future date
        day_of_week=DayOfWeek.MONDAY,
        start_time="10:00",
        end_time="10:30",
        slot_duration=30,
        is_available=True,
        active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def mock_expired_availability_slot():
    now = utc_now()
    return DoctorAvailabilityInDB(
        id="507f1f77bcf86cd799439055",
        doctor_id="507f1f77bcf86cd799439033",
        date="2020-01-01", # past date
        day_of_week=DayOfWeek.MONDAY,
        start_time="10:00",
        end_time="10:30",
        slot_duration=30,
        is_available=True,
        active=True,
        created_at=now,
        updated_at=now
    )

def test_list_doctors_success(client, patient_user, mock_discovery_doctor):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_service = AsyncMock()
    mock_service.search_verified_doctors.return_value = [mock_discovery_doctor]
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_service

    response = client.get("/api/v1/doctors?search=John&specialization=Cardiology&min_experience=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["doctors"]) == 1
    assert data["data"]["doctors"][0]["name"] == "Dr. Verified John"
    mock_service.search_verified_doctors.assert_called_once_with(
        name_query="John",
        specialization="Cardiology",
        min_experience=10
    )


def test_get_doctor_details_success(client, patient_user, mock_discovery_doctor):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_service = AsyncMock()
    mock_service.get_verified_doctor_by_id.return_value = mock_discovery_doctor
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_service

    response = client.get("/api/v1/doctors/507f1f77bcf86cd799439033")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "507f1f77bcf86cd799439033"
    assert data["data"]["name"] == "Dr. Verified John"
    mock_service.get_verified_doctor_by_id.assert_called_once_with("507f1f77bcf86cd799439033")


def test_get_doctor_details_not_found(client, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_service = AsyncMock()
    mock_service.get_verified_doctor_by_id.return_value = None
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_service

    response = client.get("/api/v1/doctors/non_existent_id")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False


def test_get_doctor_availability_success_filters_expired(
    client, patient_user, mock_discovery_doctor, mock_availability_slot, mock_expired_availability_slot
):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_verified_doctor_by_id.return_value = mock_discovery_doctor
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_avail_service = AsyncMock()
    mock_avail_service.get_active_availability.return_value = [
        mock_availability_slot,
        mock_expired_availability_slot,
    ]
    
    # Mock to_response
    def fake_to_response(slot):
        return DoctorAvailabilityResponse(
            id=slot.id,
            doctor_id=slot.doctor_id,
            date=slot.date,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            slot_duration=slot.slot_duration,
            is_available=slot.is_available,
            active=slot.active,
            created_at=slot.created_at,
            updated_at=slot.updated_at
        )
    mock_avail_service.to_response = fake_to_response
    app.dependency_overrides[get_doctor_availability_service] = lambda: mock_avail_service

    response = client.get("/api/v1/doctors/507f1f77bcf86cd799439033/availability")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Expired slot is filtered out, only future slot remains
    assert len(data["data"]["slots"]) == 1
    assert data["data"]["slots"][0]["id"] == "507f1f77bcf86cd799439044"


def test_get_doctor_availability_for_unverified_doctor(client, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_verified_doctor_by_id.return_value = None
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    response = client.get("/api/v1/doctors/pending_doctor_id/availability")
    assert response.status_code == 404
