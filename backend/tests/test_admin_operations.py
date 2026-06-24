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
    get_audit_log_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider, UserResponse
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.schemas.doctor import AdminDoctorListResponse, DoctorProfileResponse
from app.schemas.observability import AuditLogResponse
from app.models.observability import AuditLogInDB

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
        id="admin_user_id",
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
        id="patient_user_id",
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
        id="doctor_user_id",
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
def doctor_profile():
    now = utc_now()
    return DoctorProfileInDB(
        id="doctor_profile_id",
        user_id="doctor_user_id",
        specialization="Cardiology",
        qualifications=["MD"],
        experience_years=10,
        consultation_fee=500.0,
        bio="Cardiologist",
        languages=["English"],
        hospital="City Hospital",
        license_number="LIC123",
        education="Medical College",
        profile_status=DoctorProfileStatus.VERIFIED,
        average_rating=4.5,
        total_reviews=10,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def mocks():
    user_svc = AsyncMock()
    doctor_svc = AsyncMock()
    audit_svc = AsyncMock()
    auth_svc = AsyncMock()

    # Mock require_role RBAC logic
    def mock_require_role(user, required_role):
        if user.role == UserRole.ADMIN:
            return
        raise PermissionError("Forbidden")
    auth_svc.require_role = mock_require_role

    # Mock serialize conversion
    def to_response(user):
        return UserResponse(
            id=user.id,
            role=user.role,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            profile_picture=user.profile_picture,
            auth_provider=user.auth_provider,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at
        )
    user_svc.to_response = MagicMock(side_effect=to_response)

    def doctor_to_response(profile):
        return DoctorProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            specialization=profile.specialization,
            qualifications=profile.qualifications,
            experience_years=profile.experience_years,
            consultation_fee=profile.consultation_fee,
            bio=profile.bio,
            languages=profile.languages,
            hospital=profile.hospital,
            license_number=profile.license_number,
            education=profile.education,
            profile_status=profile.profile_status,
            average_rating=profile.average_rating,
            total_reviews=profile.total_reviews,
            rejection_reason=profile.rejection_reason,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    doctor_svc.to_response = MagicMock(side_effect=doctor_to_response)

    app.dependency_overrides[get_user_service] = lambda: user_svc
    app.dependency_overrides[get_doctor_profile_service] = lambda: doctor_svc
    app.dependency_overrides[get_audit_log_service] = lambda: audit_svc
    app.dependency_overrides[get_auth_service] = lambda: auth_svc

    return user_svc, doctor_svc, audit_svc, auth_svc

def test_admin_operations_non_admin_forbidden(client, mocks, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    # List users
    res = client.get("/api/v1/admin/users")
    assert res.status_code == 403

    # View user
    res = client.get("/api/v1/admin/users/some_id")
    assert res.status_code == 403

    # Activate user
    res = client.put("/api/v1/admin/users/some_id/activate")
    assert res.status_code == 403

    # Suspend user
    res = client.put("/api/v1/admin/users/some_id/suspend")
    assert res.status_code == 403

    # List doctors
    res = client.get("/api/v1/admin/doctors")
    assert res.status_code == 403

    # Suspend doctor
    res = client.put("/api/v1/admin/doctors/some_id/suspend")
    assert res.status_code == 403

    # Reactivate doctor
    res = client.put("/api/v1/admin/doctors/some_id/reactivate")
    assert res.status_code == 403

def test_list_users_success(client, mocks, admin_user, patient_user):
    user_svc, _, _, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.list_users.return_value = [admin_user, patient_user]

    res = client.get("/api/v1/admin/users?search=User&role=patient&is_active=true")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["users"]) == 2
    assert data["data"]["users"][0]["email"] == "admin@example.com"
    assert data["data"]["users"][1]["email"] == "patient@example.com"

    user_svc.list_users.assert_called_once_with(
        search="User",
        role=UserRole.PATIENT,
        is_active=True,
        limit=100,
        skip=0
    )

def test_get_user_details_success(client, mocks, admin_user, patient_user):
    user_svc, _, _, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.get_user_by_id.return_value = patient_user

    res = client.get(f"/api/v1/admin/users/{patient_user.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["id"] == patient_user.id
    assert data["data"]["email"] == patient_user.email

    user_svc.get_user_by_id.assert_called_once_with(patient_user.id)

def test_get_user_details_not_found(client, mocks, admin_user):
    user_svc, _, _, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.get_user_by_id.return_value = None

    res = client.get("/api/v1/admin/users/nonexistent")
    assert res.status_code == 404
    assert res.json()["message"] == "User not found"

def test_activate_user_success(client, mocks, admin_user, patient_user):
    user_svc, _, audit_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    inactive_patient = patient_user.model_copy(update={"is_active": False})
    user_svc.get_user_by_id.return_value = inactive_patient
    user_svc.update_user.return_value = patient_user

    res = client.put(f"/api/v1/admin/users/{patient_user.id}/activate")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["message"] == "User account activated successfully"

    user_svc.update_user.assert_called_once()
    audit_svc.create_log.assert_called_once()
    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "USER_ACTIVATED"
    assert audit_args.resource_id == patient_user.id

def test_activate_user_already_active(client, mocks, admin_user, patient_user):
    user_svc, _, audit_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.get_user_by_id.return_value = patient_user

    res = client.put(f"/api/v1/admin/users/{patient_user.id}/activate")
    assert res.status_code == 200
    assert res.json()["message"] == "User account is already active"
    user_svc.update_user.assert_not_called()
    audit_svc.create_log.assert_not_called()

def test_suspend_user_success(client, mocks, admin_user, patient_user):
    user_svc, _, audit_svc, auth_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.get_user_by_id.return_value = patient_user
    user_svc.update_user.return_value = patient_user.model_copy(update={"is_active": False})

    res = client.put(f"/api/v1/admin/users/{patient_user.id}/suspend")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["message"] == "User account suspended successfully"

    user_svc.update_user.assert_called_once()
    auth_svc.logout_all.assert_called_once_with(patient_user.id)
    audit_svc.create_log.assert_called_once()
    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "USER_SUSPENDED"
    assert audit_args.resource_id == patient_user.id

def test_suspend_user_lockout_safety(client, mocks, admin_user):
    user_svc, _, audit_svc, auth_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.get_user_by_id.return_value = admin_user
    # Only 1 active admin exists
    user_svc.count_active_admins.return_value = 1

    res = client.put(f"/api/v1/admin/users/{admin_user.id}/suspend")
    assert res.status_code == 400
    assert "Cannot suspend the last active administrator" in res.json()["message"]

    user_svc.update_user.assert_not_called()
    auth_svc.logout_all.assert_not_called()
    audit_svc.create_log.assert_not_called()

def test_list_doctors_success(client, mocks, admin_user, doctor_user, doctor_profile):
    user_svc, doctor_svc, _, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    doctor_svc.profile_repository = AsyncMock()
    doctor_svc.profile_repository.get_many.return_value = [doctor_profile]
    user_svc.get_user_by_id.return_value = doctor_user

    res = client.get("/api/v1/admin/doctors?specialization=Cardio&verification_status=verified")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["doctors"]) == 1
    assert data["data"]["doctors"][0]["id"] == doctor_profile.id
    assert data["data"]["doctors"][0]["full_name"] == doctor_user.full_name
    assert data["data"]["doctors"][0]["is_active"] is True

def test_suspend_doctor_success(client, mocks, admin_user, doctor_user, doctor_profile):
    user_svc, doctor_svc, audit_svc, auth_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    doctor_svc.get_profile_by_id.return_value = doctor_profile
    doctor_svc.profile_repository = AsyncMock()
    user_svc.get_user_by_id.return_value = doctor_user

    res = client.put(f"/api/v1/admin/doctors/{doctor_profile.id}/suspend")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["message"] == "Doctor practitioner suspended successfully"

    doctor_svc.profile_repository.update_status.assert_called_once_with(doctor_profile.id, DoctorProfileStatus.SUSPENDED)
    user_svc.update_user.assert_called_once()
    auth_svc.logout_all.assert_called_once_with(doctor_profile.user_id)
    audit_svc.create_log.assert_called_once()
    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "DOCTOR_SUSPENDED"

def test_reactivate_doctor_success(client, mocks, admin_user, doctor_user, doctor_profile):
    user_svc, doctor_svc, audit_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    suspended_profile = doctor_profile.model_copy(update={"profile_status": DoctorProfileStatus.SUSPENDED})
    doctor_svc.get_profile_by_id.return_value = suspended_profile
    doctor_svc.profile_repository = AsyncMock()
    user_svc.get_user_by_id.return_value = doctor_user

    res = client.put(f"/api/v1/admin/doctors/{doctor_profile.id}/reactivate")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["message"] == "Doctor practitioner reactivated successfully"

    doctor_svc.profile_repository.update_status.assert_called_once_with(doctor_profile.id, DoctorProfileStatus.VERIFIED)
    user_svc.update_user.assert_called_once()
    audit_svc.create_log.assert_called_once()
    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "DOCTOR_REACTIVATED"
