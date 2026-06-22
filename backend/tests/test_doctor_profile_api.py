import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_doctor_profile_service,
    get_doctor_document_service,
    require_verified_doctor,
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
        bio="Experienced doctor",
        languages=["English"],
        education="MBBS, MD",
        profile_status=DoctorProfileStatus.VERIFIED,
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
        document_type=DocumentType.LICENSE,
        document_url="https://example.com/license.pdf",
        verification_status=DocumentVerificationStatus.APPROVED,
        uploaded_at=now
    )

@pytest.fixture
def mocks(verified_doctor_profile, sample_document):
    profile_svc = AsyncMock()
    document_svc = AsyncMock()

    profile_response = DoctorProfileResponse(
        id=verified_doctor_profile.id,
        user_id=verified_doctor_profile.user_id,
        specialization=verified_doctor_profile.specialization,
        qualifications=verified_doctor_profile.qualifications,
        experience_years=verified_doctor_profile.experience_years,
        consultation_fee=verified_doctor_profile.consultation_fee,
        bio=verified_doctor_profile.bio,
        languages=verified_doctor_profile.languages,
        hospital=verified_doctor_profile.hospital,
        license_number=verified_doctor_profile.license_number,
        education=verified_doctor_profile.education,
        profile_status=verified_doctor_profile.profile_status,
        average_rating=verified_doctor_profile.average_rating,
        total_reviews=verified_doctor_profile.total_reviews,
        created_at=verified_doctor_profile.created_at,
        updated_at=verified_doctor_profile.updated_at
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


def test_get_doctor_profile_success(client, mocks, verified_doctor_profile, sample_document):
    profile_svc, document_svc = mocks
    app.dependency_overrides[require_verified_doctor] = lambda: verified_doctor_profile

    document_svc.get_documents_by_doctor.return_value = [sample_document]

    response = client.get("/api/v1/doctor/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["profile"]["id"] == verified_doctor_profile.id
    assert len(data["data"]["documents"]) == 1
    assert data["data"]["documents"][0]["verification_status"] == "approved"


def test_update_doctor_profile_success(client, mocks, verified_doctor_profile, sample_document):
    profile_svc, document_svc = mocks
    app.dependency_overrides[require_verified_doctor] = lambda: verified_doctor_profile

    updated_profile = verified_doctor_profile.model_copy()
    updated_profile.bio = "New updated biography text"
    updated_profile.consultation_fee = 1200.0

    profile_svc.update_doctor_profile_management.return_value = updated_profile
    document_svc.get_documents_by_doctor.return_value = [sample_document]

    updated_response = DoctorProfileResponse(
        id=updated_profile.id,
        user_id=updated_profile.user_id,
        specialization=updated_profile.specialization,
        qualifications=updated_profile.qualifications,
        experience_years=updated_profile.experience_years,
        consultation_fee=updated_profile.consultation_fee,
        bio=updated_profile.bio,
        languages=updated_profile.languages,
        profile_status=updated_profile.profile_status,
        average_rating=updated_profile.average_rating,
        total_reviews=updated_profile.total_reviews,
        created_at=updated_profile.created_at,
        updated_at=updated_profile.updated_at
    )
    profile_svc.to_response = MagicMock(return_value=updated_response)

    payload = {
        "bio": "New updated biography text",
        "consultation_fee": 1200.0,
        "languages": ["English", "German"],
        "education": "MBBS, MD, DM",
        "experience_years": 11
    }

    response = client.put("/api/v1/doctor/profile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["profile"]["bio"] == "New updated biography text"
    assert data["data"]["profile"]["consultation_fee"] == 1200.0


def test_update_doctor_profile_ignores_unallowed_fields(client, mocks, verified_doctor_profile, sample_document):
    profile_svc, document_svc = mocks
    app.dependency_overrides[require_verified_doctor] = lambda: verified_doctor_profile

    # Mock the update call to receive payload and return verified profile unmodified for unallowed fields
    profile_svc.update_doctor_profile_management.return_value = verified_doctor_profile
    document_svc.get_documents_by_doctor.return_value = [sample_document]

    # Payload contains specialization and profile_status which are not in the update schema
    payload = {
        "bio": "Experienced doctor",
        "specialization": "Neurology",  # Not allowed
        "profile_status": "rejected"    # Not allowed
    }

    response = client.put("/api/v1/doctor/profile", json=payload)
    assert response.status_code == 200
    # Assert service update method was called. The schema ignores neurology and status updates.
    profile_svc.update_doctor_profile_management.assert_called_once()
    passed_schema = profile_svc.update_doctor_profile_management.call_args[0][1]
    assert not hasattr(passed_schema, "specialization")
    assert not hasattr(passed_schema, "profile_status")


def test_profile_guard_restrictions(client, mocks, patient_user, verified_doctor_user):
    # Bypass verified mock to test require_verified_doctor dependency behavior
    
    # 1. Patient role
    app.dependency_overrides[get_current_user] = lambda: patient_user
    response = client.get("/api/v1/doctor/profile")
    assert response.status_code == 403

    # 2. Doctor user with pending status
    app.dependency_overrides[get_current_user] = lambda: verified_doctor_user
    profile_svc, _ = mocks
    
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

    response = client.get("/api/v1/doctor/profile")
    assert response.status_code == 403
