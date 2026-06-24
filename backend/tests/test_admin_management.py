import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_user_service,
    get_audit_log_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider, UserResponse
from app.models.observability import AuditLogInDB
from app.schemas.observability import AuditLogResponse
from app.schemas.admin import AdminCreateResponse, AdminDetailResponse

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
def mocks():
    user_svc = AsyncMock()
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

    def audit_to_response(log):
        return AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            old_value=log.old_value,
            new_value=log.new_value,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at
        )
    audit_svc.to_response = MagicMock(side_effect=audit_to_response)

    app.dependency_overrides[get_user_service] = lambda: user_svc
    app.dependency_overrides[get_audit_log_service] = lambda: audit_svc
    app.dependency_overrides[get_auth_service] = lambda: auth_svc

    return user_svc, audit_svc


def test_admin_management_non_admin_forbidden(client, mocks, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user

    # Trying to list admins
    res = client.get("/api/v1/admin/admins")
    assert res.status_code == 403

    # Trying to get admin detail
    res = client.get("/api/v1/admin/admins/507f1f77bcf86cd799439000")
    assert res.status_code == 403

    # Trying to create admin
    res = client.post("/api/v1/admin/admins", json={"full_name": "New Admin", "email": "newadmin@example.com"})
    assert res.status_code == 403

    # Trying to enable admin
    res = client.put("/api/v1/admin/admins/507f1f77bcf86cd799439000/enable")
    assert res.status_code == 403

    # Trying to disable admin
    res = client.put("/api/v1/admin/admins/507f1f77bcf86cd799439000/disable")
    assert res.status_code == 403


def test_list_admins_success(client, mocks, admin_user):
    user_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.list_admins.return_value = [admin_user]

    res = client.get("/api/v1/admin/admins")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["admins"]) == 1
    assert data["data"]["admins"][0]["email"] == "admin@example.com"
    assert data["data"]["admins"][0]["role"] == "admin"


def test_get_admin_details_success(client, mocks, admin_user):
    user_svc, audit_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.get_user_by_id.return_value = admin_user
    
    now = utc_now()
    sample_log = AuditLogInDB(
        id="audit_log_123",
        user_id=admin_user.id,
        action="ADMIN_CREATED",
        resource_type="admin",
        resource_id=admin_user.id,
        old_value=None,
        new_value={"email": admin_user.email},
        ip_address="127.0.0.1",
        user_agent="pytest",
        created_at=now
    )
    audit_svc.get_admin_audit_logs.return_value = [sample_log]

    res = client.get(f"/api/v1/admin/admins/{admin_user.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["profile"]["id"] == admin_user.id
    assert data["data"]["account_status"]["is_active"] is True
    assert len(data["data"]["audit_summary"]) == 1
    assert data["data"]["audit_summary"][0]["action"] == "ADMIN_CREATED"


def test_get_admin_details_not_found(client, mocks, admin_user, patient_user):
    user_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    # Mock admin not found (None)
    user_svc.get_user_by_id.return_value = None
    res = client.get("/api/v1/admin/admins/invalid_id")
    assert res.status_code == 404

    # Mock user is found but is not an admin (is a patient)
    user_svc.get_user_by_id.return_value = patient_user
    res = client.get(f"/api/v1/admin/admins/{patient_user.id}")
    assert res.status_code == 404


def test_create_admin_success(client, mocks, admin_user):
    user_svc, audit_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    now = utc_now()
    new_admin_in_db = UserInDB(
        id="507f1f77bcf86cd799439088",
        email="newadmin@example.com",
        password_hash="hashed_temp_pwd",
        full_name="New Admin",
        role=UserRole.ADMIN,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    user_svc.create_admin.return_value = (new_admin_in_db, "TempPass123!")

    res = client.post(
        "/api/v1/admin/admins",
        json={"full_name": "New Admin", "email": "newadmin@example.com"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["email"] == "newadmin@example.com"
    assert data["data"]["temporary_password"] == "TempPass123!"

    user_svc.create_admin.assert_called_once_with(full_name="New Admin", email="newadmin@example.com")
    audit_svc.create_log.assert_called_once()
    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "ADMIN_CREATED"
    assert audit_args.resource_id == new_admin_in_db.id


def test_create_admin_duplicate_email(client, mocks, admin_user):
    user_svc, _ = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.create_admin.side_effect = ValueError("User with email newadmin@example.com already exists")

    res = client.post(
        "/api/v1/admin/admins",
        json={"full_name": "New Admin", "email": "newadmin@example.com"}
    )
    assert res.status_code == 400
    assert res.json()["message"] == "User with email newadmin@example.com already exists"


def test_enable_admin_success(client, mocks, admin_user):
    user_svc, audit_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    inactive_admin = admin_user.model_copy(update={"is_active": False})
    user_svc.get_user_by_id.return_value = inactive_admin
    user_svc.update_user_role.return_value = admin_user

    res = client.put(f"/api/v1/admin/admins/{admin_user.id}/enable")
    assert res.status_code == 200
    assert res.json()["success"] is True

    user_svc.update_user_role.assert_called_once_with(admin_user.id, UserRole.ADMIN, is_active=True)
    audit_svc.create_log.assert_called_once()
    assert audit_svc.create_log.call_args[0][0].action == "ADMIN_ENABLED"


def test_enable_admin_already_active(client, mocks, admin_user):
    user_svc, audit_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.get_user_by_id.return_value = admin_user

    res = client.put(f"/api/v1/admin/admins/{admin_user.id}/enable")
    assert res.status_code == 200
    assert res.json()["message"] == "Administrator account is already active"
    user_svc.update_user_role.assert_not_called()
    audit_svc.create_log.assert_not_called()


def test_disable_admin_success(client, mocks, admin_user):
    user_svc, audit_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.get_user_by_id.return_value = admin_user
    # Mock multiple active admins so lockout safety is satisfied
    user_svc.count_active_admins.return_value = 2
    
    disabled_admin = admin_user.model_copy(update={"is_active": False})
    user_svc.update_user_role.return_value = disabled_admin

    res = client.put(f"/api/v1/admin/admins/{admin_user.id}/disable")
    assert res.status_code == 200
    assert res.json()["success"] is True

    user_svc.update_user_role.assert_called_once_with(admin_user.id, UserRole.ADMIN, is_active=False)
    audit_svc.create_log.assert_called_once()
    assert audit_svc.create_log.call_args[0][0].action == "ADMIN_DISABLED"


def test_disable_admin_lockout_safety(client, mocks, admin_user):
    user_svc, audit_svc = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.get_user_by_id.return_value = admin_user
    # Mock only 1 active admin (the one we are trying to disable)
    user_svc.count_active_admins.return_value = 1

    res = client.put(f"/api/v1/admin/admins/{admin_user.id}/disable")
    assert res.status_code == 400
    assert "Cannot disable the last active administrator" in res.json()["message"]

    user_svc.update_user_role.assert_not_called()
    audit_svc.create_log.assert_not_called()
