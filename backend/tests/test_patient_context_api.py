"""
Nura - Patient Context API Integration Tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_patient_context_service,
    get_doctor_profile_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.patient_context import PatientContextResponse, PatientContextMetadata


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def patient_user():
    return UserInDB(
        id="pat-111",
        email="patient@example.com",
        password_hash="pass_hash",
        full_name="John Patient",
        role=UserRole.PATIENT,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True
    )


@pytest.fixture
def doctor_user():
    return UserInDB(
        id="doc-222",
        email="doctor@example.com",
        password_hash="pass_hash",
        full_name="Jane Doctor",
        role=UserRole.DOCTOR,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True
    )


@pytest.fixture
def admin_user():
    return UserInDB(
        id="adm-333",
        email="admin@example.com",
        password_hash="pass_hash",
        full_name="Jack Admin",
        role=UserRole.ADMIN,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True
    )


def test_context_me_endpoint_patient_only(client, patient_user):
    """Verify that patient can retrieve their own context successfully"""
    mock_service = MagicMock()
    
    metadata = {
        "patient_id": "pat-111",
        "generated_at": "2026-06-26T12:00:00Z",
        "sources_used": ["users"],
        "sections_returned": ["patient_profile"],
        "estimated_tokens": 100,
        "context_version": "1.0.0"
    }
    
    mock_service.assemble_context = AsyncMock(return_value=PatientContextResponse(
        patient_profile={"id": "pat-111", "full_name": "John Patient"},
        metadata=metadata
    ))

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_patient_context_service] = lambda: mock_service

    response = client.get("/api/v1/ai/context/me")
    assert response.status_code == 200
    
    data = response.json()
    assert data["patient_profile"]["id"] == "pat-111"
    assert data["metadata"]["estimated_tokens"] == 100


def test_context_me_endpoint_doctor_rejected(client, doctor_user):
    """Verify that a doctor role is rejected from get_patient_context_me"""
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    response = client.get("/api/v1/ai/context/me")
    assert response.status_code == 403


def test_context_id_endpoint_admin_allowed(client, admin_user):
    """Verify that administrator can retrieve context for any patient ID without treatment check"""
    mock_service = MagicMock()
    
    metadata = {
        "patient_id": "pat-777",
        "generated_at": "2026-06-26T12:00:00Z",
        "sources_used": ["users"],
        "sections_returned": ["patient_profile"],
        "estimated_tokens": 100,
        "context_version": "1.0.0"
    }
    mock_service.assemble_context = AsyncMock(return_value=PatientContextResponse(
        patient_profile={"id": "pat-777", "full_name": "Alien Patient"},
        metadata=metadata
    ))

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_patient_context_service] = lambda: mock_service

    response = client.get("/api/v1/ai/context/pat-777")
    assert response.status_code == 200
    
    data = response.json()
    assert data["patient_profile"]["id"] == "pat-777"


def test_context_id_endpoint_doctor_treated_allowed(client, doctor_user):
    """Verify that a verified doctor can retrieve context if they have treated the patient"""
    mock_service = MagicMock()
    mock_service.appointment_repository = MagicMock()
    mock_service.appointment_repository.exists = AsyncMock(return_value=True) # Treated!
    
    metadata = {
        "patient_id": "pat-888",
        "generated_at": "2026-06-26T12:00:00Z",
        "sources_used": ["users"],
        "sections_returned": ["patient_profile"],
        "estimated_tokens": 100,
        "context_version": "1.0.0"
    }
    mock_service.assemble_context = AsyncMock(return_value=PatientContextResponse(
        patient_profile={"id": "pat-888", "full_name": "Treated Patient"},
        metadata=metadata
    ))

    # Mock doctor profile
    mock_doctor_profile = MagicMock()
    mock_doctor_profile.id = "doc-profile-id"
    mock_doctor_profile.profile_status = "verified"
    
    mock_doctor_service = MagicMock()
    mock_doctor_service.get_profile_by_user_id = AsyncMock(return_value=mock_doctor_profile)

    app.dependency_overrides[get_current_user] = lambda: doctor_user
    app.dependency_overrides[get_patient_context_service] = lambda: mock_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_doctor_service

    response = client.get("/api/v1/ai/context/pat-888")
    assert response.status_code == 200
    assert response.json()["patient_profile"]["id"] == "pat-888"


def test_context_id_endpoint_doctor_untreated_denied(client, doctor_user):
    """Verify that a verified doctor gets 403 if they have not treated the patient"""
    mock_service = MagicMock()
    mock_service.appointment_repository = MagicMock()
    mock_service.appointment_repository.exists = AsyncMock(return_value=False)
    mock_service.consultation_repository = MagicMock()
    mock_service.consultation_repository.exists = AsyncMock(return_value=False)

    # Mock doctor profile
    mock_doctor_profile = MagicMock()
    mock_doctor_profile.id = "doc-profile-id"
    mock_doctor_profile.profile_status = "verified"
    
    mock_doctor_service = MagicMock()
    mock_doctor_service.get_profile_by_user_id = AsyncMock(return_value=mock_doctor_profile)

    app.dependency_overrides[get_current_user] = lambda: doctor_user
    app.dependency_overrides[get_patient_context_service] = lambda: mock_service
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_doctor_service

    response = client.get("/api/v1/ai/context/pat-999")
    assert response.status_code == 403
    assert "doctor has not treated" in response.json()["message"].lower()
