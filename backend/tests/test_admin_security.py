import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_user_service,
    get_audit_log_service,
    get_refresh_token_repository,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.refresh_token import RefreshTokenInDB, RefreshTokenCreate
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
        id="admin_id_123",
        email="admin@example.com",
        password_hash="hashed_pw",
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
        id="patient_id_123",
        email="patient@example.com",
        password_hash="hashed_pw",
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
    auth_svc = AsyncMock()
    token_repo = AsyncMock()

    # Configure synchronous methods
    user_svc.verify_password = MagicMock()
    auth_svc.hash_token = MagicMock()
    auth_svc.create_access_token = MagicMock()

    # Mock require_role logic
    def mock_require_role(user, required_role):
        if user.role == UserRole.ADMIN:
            return
        if user.role == UserRole.DOCTOR and required_role in (UserRole.DOCTOR, UserRole.PATIENT):
            return
        if user.role == UserRole.PATIENT and required_role == UserRole.PATIENT:
            return
        raise PermissionError("Forbidden")
    auth_svc.require_role = mock_require_role

    app.dependency_overrides[get_user_service] = lambda: user_svc
    app.dependency_overrides[get_audit_log_service] = lambda: audit_svc
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    app.dependency_overrides[get_refresh_token_repository] = lambda: token_repo

    auth_svc.refresh_token_repository = token_repo
    auth_svc.user_service = user_svc

    return user_svc, audit_svc, auth_svc, token_repo



def test_security_endpoints_non_admin_forbidden(client, mocks, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user

    # List sessions
    res = client.get("/api/v1/admin/security/sessions")
    assert res.status_code == 403

    # Revoke session
    res = client.post("/api/v1/admin/security/sessions/session_abc/revoke")
    assert res.status_code == 403


def test_admin_login_logs_audit_event(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks
    
    # Mock find user and password verification
    user_svc.get_user_by_email.return_value = admin_user
    user_svc.verify_password.return_value = True

    # Mock token generation details
    token_response = MagicMock()
    token_response.access_token = "access_token_123"
    token_response.refresh_token = "refresh_token_123"
    token_response.user.id = admin_user.id
    token_response.user.role = UserRole.ADMIN

    auth_svc._build_token_pair.return_value = (token_response, "raw_refresh", MagicMock())
    auth_svc.hash_token.return_value = "hashed_refresh"

    res = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Password123!"})
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Check that audit log was generated
    audit_svc.create_log.assert_called_once()
    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "ADMIN_LOGIN"
    assert audit_args.user_id == admin_user.id
    assert audit_args.resource_id == admin_user.id


def test_admin_logout_logs_audit_event(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks

    # Mock get session and user
    now = utc_now()
    session_record = RefreshTokenInDB(
        id="session_id_123",
        user_id=admin_user.id,
        token_hash="hashed_token_123",
        expires_at=now + timedelta(days=7),
        revoked=False,
        created_at=now,
        last_activity=now
    )
    token_repo.get_by_token_hash.return_value = session_record
    user_svc.get_user_by_id.return_value = admin_user
    token_repo.revoke_by_hash.return_value = True

    res = client.post("/api/v1/auth/logout", json={"refresh_token": "valid_token"})
    assert res.status_code == 200
    assert res.json()["success"] is True

    audit_svc.create_log.assert_called_once()
    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "ADMIN_LOGOUT"
    assert audit_args.user_id == admin_user.id


def test_admin_refresh_logs_audit_event_and_updates_activity(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks

    now = utc_now()
    session_record = RefreshTokenInDB(
        id="session_id_123",
        user_id=admin_user.id,
        token_hash="hashed_token_123",
        expires_at=now + timedelta(days=7),
        revoked=False,
        created_at=now,
        last_activity=now
    )
    token_repo.get_by_token_hash.return_value = session_record
    user_svc.get_user_by_id.return_value = admin_user
    auth_svc.create_access_token.return_value = "new_access_token"

    res = client.post("/api/v1/auth/refresh", json={"refresh_token": "valid_token"})
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Should update last activity on repository and log audit trail
    token_repo.update_last_activity.assert_called_once_with(session_record.id)
    audit_svc.create_log.assert_called_once()
    assert audit_svc.create_log.call_args[0][0].action == "ADMIN_TOKEN_REFRESH"


def test_admin_forgot_password_logs_audit_event(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks
    
    # Mock admin lookup
    user_svc.get_user_by_email.return_value = admin_user

    # Mock OTP and email services
    otp_svc = AsyncMock()
    otp_svc.send_otp.return_value = "123456"
    email_svc = AsyncMock()
    email_svc.send_password_reset_email.return_value = True

    from app.core.dependencies import get_otp_service, get_email_service
    app.dependency_overrides[get_otp_service] = lambda: otp_svc
    app.dependency_overrides[get_email_service] = lambda: email_svc

    res = client.post("/api/v1/auth/forgot-password", json={"email": "admin@example.com"})
    assert res.status_code == 200

    audit_svc.create_log.assert_called_once()
    assert audit_svc.create_log.call_args[0][0].action == "ADMIN_PASSWORD_RESET_REQUEST"


def test_admin_reset_password_logs_audit_event(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks

    # Mock verify OTP flow
    otp_svc = AsyncMock()
    latest_otp_doc = {
        "_id": "507f1f77bcf86cd799439012",
        "email": admin_user.email,
        "otp": "123456",
        "purpose": "password_reset",
        "verified": False,
        "expires_at": utc_now() + timedelta(minutes=10)
    }
    otp_svc.otp_repository.collection.find_one = AsyncMock(return_value=latest_otp_doc)
    otp_svc.verify_otp.return_value = True
    
    user_svc.get_user_by_email.return_value = admin_user
    user_svc.reset_password.return_value = True

    from app.core.dependencies import get_otp_service
    app.dependency_overrides[get_otp_service] = lambda: otp_svc

    res = client.post(
        "/api/v1/auth/reset-password",
        json={"email": "admin@example.com", "otp": "123456", "new_password": "NewAdminPassword123!"}
    )
    assert res.status_code == 200

    audit_svc.create_log.assert_called_once()
    assert audit_svc.create_log.call_args[0][0].action == "ADMIN_PASSWORD_RESET_SUCCESS"


def test_admin_change_password_logs_audit_event(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    user_svc.change_password.return_value = True

    res = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "Password123!", "new_password": "NewPassword123!"}
    )
    assert res.status_code == 200

    user_svc.change_password.assert_called_once_with(admin_user.id, "Password123!", "NewPassword123!")
    audit_svc.create_log.assert_called_once()
    assert audit_svc.create_log.call_args[0][0].action == "ADMIN_PASSWORD_CHANGED"


def test_session_listing_success(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    now = utc_now()
    session_list = [
        RefreshTokenInDB(
            id="session_1",
            user_id=admin_user.id,
            token_hash="hashed_1",
            expires_at=now + timedelta(days=7),
            revoked=False,
            created_at=now,
            last_activity=now
        )
    ]
    token_repo.get_all_by_user.return_value = session_list

    res = client.get("/api/v1/admin/security/sessions")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["sessions"]) == 1
    assert data["data"]["sessions"][0]["id"] == "session_1"
    assert data["data"]["sessions"][0]["revoked"] is False


def test_session_revocation_success(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    now = utc_now()
    session_record = RefreshTokenInDB(
        id="session_1",
        user_id=admin_user.id,
        token_hash="hashed_1",
        expires_at=now + timedelta(days=7),
        revoked=False,
        created_at=now,
        last_activity=now
    )
    token_repo.get.return_value = session_record
    token_repo.revoke_token.return_value = session_record.model_copy(update={"revoked": True})

    res = client.post("/api/v1/admin/security/sessions/session_1/revoke")
    assert res.status_code == 200
    assert res.json()["success"] is True

    token_repo.revoke_token.assert_called_once_with("session_1")
    audit_svc.create_log.assert_called_once()
    audit_args = audit_svc.create_log.call_args[0][0]
    assert audit_args.action == "ADMIN_SESSION_REVOKED"
    assert audit_args.resource_id == "session_1"


def test_session_revocation_already_revoked(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    now = utc_now()
    session_record = RefreshTokenInDB(
        id="session_1",
        user_id=admin_user.id,
        token_hash="hashed_1",
        expires_at=now + timedelta(days=7),
        revoked=True,
        created_at=now,
        last_activity=now
    )
    token_repo.get.return_value = session_record

    res = client.post("/api/v1/admin/security/sessions/session_1/revoke")
    assert res.status_code == 400
    assert "already revoked" in res.json()["message"]

    token_repo.revoke_token.assert_not_called()
    audit_svc.create_log.assert_not_called()


def test_session_revocation_unauthorized_owner(client, mocks, admin_user):
    user_svc, audit_svc, auth_svc, token_repo = mocks
    app.dependency_overrides[get_current_user] = lambda: admin_user

    now = utc_now()
    # Session belongs to different user
    session_record = RefreshTokenInDB(
        id="session_1",
        user_id="other_admin_id",
        token_hash="hashed_1",
        expires_at=now + timedelta(days=7),
        revoked=False,
        created_at=now,
        last_activity=now
    )
    token_repo.get.return_value = session_record

    res = client.post("/api/v1/admin/security/sessions/session_1/revoke")
    assert res.status_code == 403
    token_repo.revoke_token.assert_not_called()
