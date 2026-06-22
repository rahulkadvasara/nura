import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_doctor_profile_service,
    get_doctor_document_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.doctor import (
    DoctorProfileInDB,
    DoctorProfileStatus,
    DoctorDocumentInDB,
    DocumentType,
    DocumentVerificationStatus,
)
from app.schemas.doctor import DoctorProfileResponse, DoctorDocumentResponse

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
def doctor_user():
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
def sample_profile():
    now = utc_now()
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439033",
        user_id="507f1f77bcf86cd799439011",
        specialization="Cardiology",
        qualifications=[],
        experience_years=10,
        consultation_fee=1000.0,
        bio="Experienced doctor",
        languages=["English", "Hindi"],
        hospital="City General",
        license_number="LIC123",
        education="MBBS, MD",
        profile_status=DoctorProfileStatus.PENDING,
        average_rating=0.0,
        total_reviews=0,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def sample_document():
    now = utc_now()
    return DoctorDocumentInDB(
        id="507f1f77bcf86cd799439044",
        doctor_id="507f1f77bcf86cd799439033",
        document_type=DocumentType.DEGREE,
        document_url="https://example.com/degree.pdf",
        verification_status=DocumentVerificationStatus.PENDING,
        uploaded_at=now
    )

@pytest.fixture
def mocks(sample_profile, sample_document):
    profile_svc = AsyncMock()
    document_svc = AsyncMock()

    # Setup responses
    profile_response = DoctorProfileResponse(
        id=sample_profile.id,
        user_id=sample_profile.user_id,
        specialization=sample_profile.specialization,
        qualifications=sample_profile.qualifications,
        experience_years=sample_profile.experience_years,
        consultation_fee=sample_profile.consultation_fee,
        bio=sample_profile.bio,
        languages=sample_profile.languages,
        hospital=sample_profile.hospital,
        license_number=sample_profile.license_number,
        education=sample_profile.education,
        profile_status=sample_profile.profile_status,
        average_rating=sample_profile.average_rating,
        total_reviews=sample_profile.total_reviews,
        created_at=sample_profile.created_at,
        updated_at=sample_profile.updated_at
    )
    profile_svc.to_response = MagicMock(return_value=profile_response)

    doc_response = DoctorDocumentResponse(
        id=sample_document.id,
        doctor_id=sample_document.doctor_id,
        document_type=sample_document.document_type,
        document_url=sample_document.document_url,
        verification_status=sample_document.verification_status,
        uploaded_at=sample_document.uploaded_at
    )
    document_svc.to_response = MagicMock(return_value=doc_response)

    app.dependency_overrides[get_doctor_profile_service] = lambda: profile_svc
    app.dependency_overrides[get_doctor_document_service] = lambda: document_svc

    return profile_svc, document_svc


def test_apply_doctor_success(client, mocks, patient_user, sample_profile, sample_document):
    profile_svc, document_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: patient_user

    profile_svc.get_profile_by_user_id.return_value = None
    profile_svc.create_profile.return_value = sample_profile
    document_svc.upload_document.return_value = sample_document
    document_svc.get_documents_by_doctor.return_value = [sample_document]

    payload = {
        "specialization": "Cardiology",
        "experience_years": 10,
        "consultation_fee": 1000.0,
        "bio": "Experienced doctor",
        "education": "MBBS, MD",
        "languages": ["English", "Hindi"],
        "hospital": "City General",
        "license_number": "LIC123",
        "degree_certificate_url": "https://example.com/degree.pdf",
        "medical_license_url": "https://example.com/license.pdf",
        "identity_proof_url": "https://example.com/id.pdf"
    }

    response = client.post("/api/v1/doctor/apply", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["application_status"] == "Pending Review"
    assert data["data"]["profile"]["specialization"] == "Cardiology"


def test_apply_doctor_duplicate(client, mocks, patient_user, sample_profile):
    profile_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: patient_user

    profile_svc.get_profile_by_user_id.return_value = sample_profile

    payload = {
        "specialization": "Cardiology",
        "experience_years": 10,
        "consultation_fee": 1000.0,
        "bio": "Experienced doctor",
        "education": "MBBS, MD",
        "languages": ["English", "Hindi"],
        "hospital": "City General",
        "license_number": "LIC123",
        "degree_certificate_url": "https://example.com/degree.pdf",
        "medical_license_url": "https://example.com/license.pdf",
        "identity_proof_url": "https://example.com/id.pdf"
    }

    response = client.post("/api/v1/doctor/apply", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "already exists" in data["message"]


def test_apply_doctor_insufficient_role(client, mocks, doctor_user):
    app.dependency_overrides[get_current_user] = lambda: doctor_user

    payload = {
        "specialization": "Cardiology",
        "experience_years": 10,
        "consultation_fee": 1000.0,
        "education": "MBBS",
        "languages": ["English"],
        "degree_certificate_url": "https://example.com/degree.pdf",
        "medical_license_url": "https://example.com/license.pdf",
        "identity_proof_url": "https://example.com/id.pdf"
    }

    response = client.post("/api/v1/doctor/apply", json=payload)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False


def test_get_application_success(client, mocks, patient_user, sample_profile, sample_document):
    profile_svc, document_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: patient_user

    profile_svc.get_profile_by_user_id.return_value = sample_profile
    document_svc.get_documents_by_doctor.return_value = [sample_document]

    response = client.get("/api/v1/doctor/application")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["application_status"] == "Pending Review"


def test_get_application_not_found(client, mocks, patient_user):
    profile_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: patient_user

    profile_svc.get_profile_by_user_id.return_value = None

    response = client.get("/api/v1/doctor/application")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False


def test_update_application_success(client, mocks, patient_user, sample_profile, sample_document):
    profile_svc, document_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: patient_user

    profile_svc.get_profile_by_user_id.return_value = sample_profile
    profile_svc.update_profile.return_value = sample_profile
    document_svc.get_documents_by_doctor.return_value = [sample_document]
    document_svc.document_repository = AsyncMock()

    payload = {
        "specialization": "Pediatrics",
        "experience_years": 12,
        "consultation_fee": 1200.0,
        "degree_certificate_url": "https://example.com/new_degree.pdf"
    }

    response = client.put("/api/v1/doctor/application", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["profile"]["id"] == sample_profile.id


def test_update_application_not_pending(client, mocks, patient_user, sample_profile):
    profile_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: patient_user

    sample_profile.profile_status = DoctorProfileStatus.VERIFIED
    profile_svc.get_profile_by_user_id.return_value = sample_profile

    payload = {
        "specialization": "Pediatrics"
    }

    response = client.put("/api/v1/doctor/application", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "pending" in data["message"]
