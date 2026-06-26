import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_user_service,
    get_doctor_profile_service,
    get_doctor_document_service,
    get_audit_log_service,
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
def admin_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439000",
        email="admin@example.com",
        password_hash="hashed",
        full_name="Admin User",
        role=UserRole.ADMIN,
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
        rejection_reason=None,
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
    user_svc = AsyncMock()
    profile_svc = AsyncMock()
    document_svc = AsyncMock()
    audit_svc = AsyncMock()
    auth_svc = MagicMock()

    # Mock require_role RBAC logic
    def mock_require_role(user, required_role):
        if user.role == UserRole.ADMIN:
            return
        if user.role == UserRole.DOCTOR and required_role in (UserRole.DOCTOR, UserRole.PATIENT):
            return
        if user.role == UserRole.PATIENT and required_role == UserRole.PATIENT:
            return
        raise PermissionError("Forbidden")
    auth_svc.require_role = mock_require_role

    # Mocks serialization conversion
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
        rejection_reason=sample_profile.rejection_reason,
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

    app.dependency_overrides[get_user_service] = lambda: user_svc
    app.dependency_overrides[get_doctor_profile_service] = lambda: profile_svc
    app.dependency_overrides[get_doctor_document_service] = lambda: document_svc
    app.dependency_overrides[get_audit_log_service] = lambda: audit_svc
    app.dependency_overrides[get_auth_service] = lambda: auth_svc

    return user_svc, profile_svc, document_svc, audit_svc


def test_admin_endpoints_non_admin_forbidden(client, mocks, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user

    # Trying to fetch pending list
    res = client.get("/api/v1/admin/doctors/pending")
    assert res.status_code == 403

    # Trying to approve
    res = client.post("/api/v1/admin/doctors/profile_123/approve", json={})
    assert res.status_code == 403

    # Trying to reject
    res = client.post("/api/v1/admin/doctors/profile_123/reject", json={"rejection_reason": "bad documents"})
    assert res.status_code == 403


def test_get_pending_doctors_success(client, mocks, admin_user, patient_user, sample_profile):
    user_svc, profile_svc, _, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    profile_svc.list_by_status.return_value = [sample_profile]
    user_svc.get_user_by_id.return_value = patient_user

    res = client.get("/api/v1/admin/doctors/pending")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["doctors"]) == 1
    assert data["data"]["doctors"][0]["full_name"] == "Patient User"
    assert data["data"]["doctors"][0]["email"] == "patient@example.com"
    assert data["data"]["doctors"][0]["specialization"] == "Cardiology"


def test_get_doctor_application_details_success(client, mocks, admin_user, patient_user, sample_profile, sample_document):
    user_svc, profile_svc, document_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    profile_svc.get_profile_by_id.return_value = sample_profile
    user_svc.get_user_by_id.return_value = patient_user
    document_svc.get_documents_by_doctor.return_value = [sample_document]

    res = client.get(f"/api/v1/admin/doctors/{sample_profile.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["profile"]["id"] == sample_profile.id
    assert data["data"]["user"]["email"] == "patient@example.com"
    assert len(data["data"]["documents"]) == 1


def test_approve_doctor_application_success(client, mocks, admin_user, patient_user, sample_profile, sample_document):
    user_svc, profile_svc, document_svc, audit_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    profile_svc.get_profile_by_id.return_value = sample_profile
    user_svc.get_user_by_id.return_value = patient_user
    
    # Mocking successful verify / update
    verified_profile = sample_profile.model_copy(update={"profile_status": DoctorProfileStatus.VERIFIED})
    profile_svc.verify_profile.return_value = verified_profile
    
    document_svc.get_documents_by_doctor.return_value = [sample_document]
    document_svc.approve_document.return_value = sample_document.model_copy(update={"verification_status": DocumentVerificationStatus.APPROVED})
    
    promoted_user = patient_user.model_copy(update={"role": UserRole.DOCTOR, "is_active": True})
    user_svc.update_user_role.return_value = promoted_user

    res = client.post(f"/api/v1/admin/doctors/{sample_profile.id}/approve", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    # Check services call hierarchy
    profile_svc.verify_profile.assert_called_once_with(sample_profile.id)
    document_svc.approve_document.assert_called_once_with(sample_document.id, admin_user.id)
    user_svc.update_user_role.assert_called_once_with(sample_profile.user_id, UserRole.DOCTOR, is_active=True)
    audit_svc.create_log.assert_called_once()
    
    # Verify audit log details
    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "DOCTOR_APPROVED"
    assert audit_args.user_id == admin_user.id
    assert audit_args.resource_id == sample_profile.id


def test_reject_doctor_application_success(client, mocks, admin_user, patient_user, sample_profile, sample_document):
    user_svc, profile_svc, document_svc, audit_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    profile_svc.get_profile_by_id.return_value = sample_profile
    
    rejected_profile = sample_profile.model_copy(update={"profile_status": DoctorProfileStatus.REJECTED, "rejection_reason": "Missing diploma"})
    profile_svc.reject_profile.return_value = rejected_profile
    
    document_svc.get_documents_by_doctor.return_value = [sample_document]
    document_svc.reject_document.return_value = sample_document.model_copy(update={"verification_status": DocumentVerificationStatus.REJECTED})

    res = client.post(f"/api/v1/admin/doctors/{sample_profile.id}/reject", json={"rejection_reason": "Missing diploma"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    profile_svc.reject_profile.assert_called_once_with(sample_profile.id, "Missing diploma")
    document_svc.reject_document.assert_called_once_with(sample_document.id, admin_user.id)
    user_svc.update_user_role.assert_not_called()  # User remains patient
    audit_svc.create_log.assert_called_once()

    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "DOCTOR_REJECTED"
    assert audit_args.user_id == admin_user.id
    assert audit_args.resource_id == sample_profile.id
    assert audit_args.new_value["rejection_reason"] == "Missing diploma"
