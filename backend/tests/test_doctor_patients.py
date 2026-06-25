import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_doctor_profile_service,
    get_doctor_patient_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.schemas.doctor_patient import DoctorPatientSummary, DoctorPatientListResponse, DoctorPatientDetailResponse
from app.schemas.appointment import AppointmentResponse, ConsultationResponse
from app.schemas.report import ReportResponse, HealthInsightResponse
from app.schemas.reminder import ReminderResponse
from app.schemas.chat import ChatSessionResponse
from app.models.user import UserResponse

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
def unverified_doctor_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439004",
        email="unverified@example.com",
        password_hash="hashed_pw",
        full_name="Unverified Doctor",
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
def unverified_doctor_profile():
    now = utc_now()
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439014",
        user_id="507f1f77bcf86cd799439004",
        specialization="Cardiology",
        qualifications=["MBBS"],
        experience_years=3,
        consultation_fee=300.0,
        bio="Unverified",
        languages=["English"],
        profile_status=DoctorProfileStatus.PENDING,
        created_at=now,
        updated_at=now
    )

def test_list_patients_unauthorized(client, unverified_doctor_user, unverified_doctor_profile):
    # Enforces that non-doctors or unverified doctors receive 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: unverified_doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = unverified_doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    response = client.get("/api/v1/doctor/patients")
    assert response.status_code == 403
    assert "verified" in response.json()["message"].lower()

def test_list_patients_success(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    # Setup dummy summaries
    summary = DoctorPatientSummary(
        patient_id="507f1f77bcf86cd799439001",
        name="Patient Name",
        age=30,
        gender="Male",
        profile_picture="http://example.com/pic.jpg",
        latest_appointment=None,
        latest_consultation=None,
        total_appointments=2,
        total_consultations=1,
        total_reports=3,
        health_risk_level="low",
    )

    mock_patient_service = AsyncMock()
    mock_patient_service.get_patients.return_value = ([summary], 1)
    app.dependency_overrides[get_doctor_patient_service] = lambda: mock_patient_service

    response = client.get("/api/v1/doctor/patients?limit=10&skip=0&sort_by=name")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 1
    assert data["data"]["patients"][0]["patient_id"] == "507f1f77bcf86cd799439001"
    assert data["data"]["patients"][0]["name"] == "Patient Name"
    assert data["data"]["patients"][0]["total_appointments"] == 2

    mock_patient_service.get_patients.assert_called_once_with(
        doctor_profile_id=doctor_profile.id,
        search=None,
        sort_by="name",
        limit=10,
        skip=0
    )

def test_list_patients_search(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_patient_service = AsyncMock()
    mock_patient_service.get_patients.return_value = ([], 0)
    app.dependency_overrides[get_doctor_patient_service] = lambda: mock_patient_service

    response = client.get("/api/v1/doctor/patients?search=John")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 0

    mock_patient_service.get_patients.assert_called_once_with(
        doctor_profile_id=doctor_profile.id,
        search="John",
        sort_by=None,
        limit=100,
        skip=0
    )

def test_get_patient_detail_success(client, doctor_user, doctor_profile, patient_user):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    detail_response = DoctorPatientDetailResponse(
        profile=UserResponse(
            id=patient_user.id,
            email=patient_user.email,
            full_name=patient_user.full_name,
            role=patient_user.role,
            is_active=patient_user.is_active,
            email_verified=patient_user.email_verified,
            profile_picture=patient_user.profile_picture,
            auth_provider=patient_user.auth_provider.value,
            created_at=patient_user.created_at,
            updated_at=patient_user.updated_at
        ),
        appointment_history=[],
        consultation_history=[],
        reports=[],
        prescriptions=[],
        health_insights=[],
        current_reminders=[],
        latest_chat_session=None
    )

    mock_patient_service = AsyncMock()
    mock_patient_service.get_patient_detail.return_value = detail_response
    app.dependency_overrides[get_doctor_patient_service] = lambda: mock_patient_service

    response = client.get(f"/api/v1/doctor/patients/{patient_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["profile"]["email"] == "patient@example.com"
    mock_patient_service.get_patient_detail.assert_called_once_with(
        doctor_profile_id=doctor_profile.id,
        patient_id=patient_user.id
    )

def test_get_patient_detail_unrelated_blocked(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_patient_service = AsyncMock()
    mock_patient_service.get_patient_detail.side_effect = ValueError("Patient not found or access denied")
    app.dependency_overrides[get_doctor_patient_service] = lambda: mock_patient_service

    response = client.get("/api/v1/doctor/patients/unrelated_id")
    assert response.status_code == 404
    assert "access denied" in response.json()["message"].lower()

def test_list_patients_empty(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_patient_service = AsyncMock()
    mock_patient_service.get_patients.return_value = ([], 0)
    app.dependency_overrides[get_doctor_patient_service] = lambda: mock_patient_service

    response = client.get("/api/v1/doctor/patients")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["patients"] == []
    assert data["data"]["total"] == 0
