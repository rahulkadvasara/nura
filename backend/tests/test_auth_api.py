"""
Nura - Auth API Integration Tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.main import app
from app.core.dependencies import get_user_service, get_otp_service, get_email_service, get_auth_service, get_current_user
from app.models import UserInDB, UserRole, AuthProvider, OTPVerificationInDB, OTPPurpose, RefreshTokenCreate, RefreshTokenInDB
from app.schemas.auth import TokenResponse, TokenUser


@pytest.fixture
def client():
    # Clear overrides
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mocks():
    user_svc = AsyncMock()
    otp_svc = AsyncMock()
    email_svc = AsyncMock()
    
    # Configure synchronous methods as MagicMocks
    user_svc.verify_password = MagicMock()
    user_svc.hash_password = MagicMock()
    from app.services.user_service import UserService
    user_svc.to_response = MagicMock(side_effect=lambda u: UserService.to_response(None, u))
    
    app.dependency_overrides[get_user_service] = lambda: user_svc
    app.dependency_overrides[get_otp_service] = lambda: otp_svc
    app.dependency_overrides[get_email_service] = lambda: email_svc
    
    yield user_svc, otp_svc, email_svc
    
    app.dependency_overrides.clear()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _make_user(
    email: str = "rahul@example.com",
    email_verified: bool = False,
    is_active: bool = False
) -> UserInDB:
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439011",
        email=email,
        password_hash="hashed_password",
        full_name="Rahul",
        role=UserRole.PATIENT,
        auth_provider=AuthProvider.LOCAL,
        email_verified=email_verified,
        is_active=is_active,
        created_at=now,
        updated_at=now
    )


def _make_otp(
    email: str = "rahul@example.com",
    otp: str = "123456",
    verified: bool = False,
    expired: bool = False
) -> OTPVerificationInDB:
    now = utc_now()
    expires_at = now - timedelta(minutes=1) if expired else now + timedelta(minutes=10)
    return OTPVerificationInDB(
        id="507f1f77bcf86cd799439012",
        email=email,
        otp=otp,
        purpose=OTPPurpose.REGISTRATION,
        expires_at=expires_at,
        verified=verified,
        created_at=now
    )


def test_register_success(client, mocks):
    """Test successful user registration"""
    mock_user_service, mock_otp_service, mock_email_service = mocks
    mock_user_service.user_exists.return_value = False
    mock_user_service.create_user.return_value = _make_user()
    mock_otp_service.send_otp.return_value = "123456"
    mock_email_service.send_otp_email.return_value = True

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Rahul",
            "email": "rahul@example.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "OTP sent successfully"

    mock_user_service.user_exists.assert_called_once_with("rahul@example.com")
    mock_user_service.create_user.assert_called_once()
    mock_otp_service.send_otp.assert_called_once_with("rahul@example.com", OTPPurpose.REGISTRATION)
    mock_email_service.send_otp_email.assert_called_once_with("rahul@example.com", "123456", "registration")


def test_register_duplicate_email(client, mocks):
    """Test register with an email that is already registered"""
    mock_user_service, _, _ = mocks
    mock_user_service.user_exists.return_value = True

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Rahul",
            "email": "rahul@example.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "already exists" in data["message"]


def test_register_invalid_password(client, mocks):
    """Test register with an invalid password (no uppercase letter, too short, etc.)"""
    # Note: validation happens at the Pydantic level, so custom exception handler in main.py will format the response
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Rahul",
            "email": "rahul@example.com",
            "password": "weak"
        }
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Validation failed"
    assert len(data["errors"]) > 0


def test_verify_otp_success(client, mocks):
    """Test successful OTP verification"""
    mock_user_service, mock_otp_service, _ = mocks
    user = _make_user(email_verified=False, is_active=False)
    otp_record = _make_otp(otp="123456")

    mock_user_service.get_user_by_email.return_value = user
    mock_otp_service.get_latest_otp.return_value = otp_record
    mock_otp_service.verify_otp.return_value = otp_record
    mock_user_service.verify_user_email.return_value = user
    mock_user_service.update_user.return_value = user

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "rahul@example.com",
            "otp": "123456"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Account verified"

    mock_user_service.get_user_by_email.assert_called_once_with("rahul@example.com")
    mock_otp_service.verify_otp.assert_called_once_with("rahul@example.com", "123456", OTPPurpose.REGISTRATION)
    mock_user_service.verify_user_email.assert_called_once_with(user.id)
    mock_user_service.update_user.assert_called_once()


def test_verify_otp_invalid_otp(client, mocks):
    """Test OTP verification with invalid code"""
    mock_user_service, mock_otp_service, _ = mocks
    user = _make_user(email_verified=False, is_active=False)
    latest_otp = _make_otp(otp="123456") # latest valid OTP is 123456

    mock_user_service.get_user_by_email.return_value = user
    mock_otp_service.get_latest_otp.return_value = latest_otp
    mock_otp_service.verify_otp.return_value = None # verification fails

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "rahul@example.com",
            "otp": "999999" # wrong OTP
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Invalid OTP"


def test_verify_otp_expired_otp(client, mocks):
    """Test OTP verification with expired code"""
    mock_user_service, mock_otp_service, _ = mocks
    user = _make_user(email_verified=False, is_active=False)
    latest_otp = _make_otp(otp="123456", expired=True)

    mock_user_service.get_user_by_email.return_value = user
    mock_otp_service.get_latest_otp.return_value = latest_otp
    mock_otp_service.verify_otp.return_value = None # verification fails since expired

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "rahul@example.com",
            "otp": "123456" # matches but is expired
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Expired OTP"


def test_verify_otp_already_verified(client, mocks):
    """Test OTP verification on already verified account"""
    mock_user_service, _, _ = mocks
    user = _make_user(email_verified=True, is_active=True)

    mock_user_service.get_user_by_email.return_value = user

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "rahul@example.com",
            "otp": "123456"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Account already verified"


@pytest.fixture
def auth_mocks(mocks):
    user_svc, otp_svc, email_svc = mocks
    auth_svc = AsyncMock()
    
    # Configure synchronous methods of AuthService as MagicMocks
    auth_svc.create_access_token = MagicMock()
    auth_svc.hash_token = MagicMock()
    auth_svc.verify_token_hash = MagicMock()
    auth_svc.has_role = MagicMock()
    auth_svc.require_role = MagicMock()
    
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    yield user_svc, otp_svc, email_svc, auth_svc


def test_login_success(client, auth_mocks):
    """Test successful login flow"""
    mock_user_service, _, _, mock_auth_service = auth_mocks
    user = _make_user(email_verified=True, is_active=True)
    
    mock_user_service.get_user_by_email.return_value = user
    mock_user_service.verify_password.return_value = True
    
    token_response = TokenResponse(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_type="bearer",
        expires_in=1800,
        user=TokenUser(
            id=user.id,
            role=user.role,
            email=user.email,
            full_name=user.full_name,
            email_verified=user.email_verified
        )
    )
    refresh_token_create = RefreshTokenCreate(
        user_id=user.id,
        token_hash="hashed_refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False
    )
    
    mock_auth_service._build_token_pair.return_value = (token_response, "test_refresh_token", refresh_token_create)
    mock_auth_service.refresh_token_repository.create_token.return_value = MagicMock()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "rahul@example.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Login successful"
    assert data["data"]["access_token"] == "test_access_token"
    assert data["data"]["refresh_token"] == "test_refresh_token"
    assert data["data"]["user"]["id"] == user.id
    assert data["data"]["user"]["role"] == user.role.value


def test_login_invalid_password(client, auth_mocks):
    """Test login with incorrect password"""
    mock_user_service, _, _, _ = auth_mocks
    user = _make_user(email_verified=True, is_active=True)
    
    mock_user_service.get_user_by_email.return_value = user
    mock_user_service.verify_password.return_value = False

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "rahul@example.com",
            "password": "WrongPassword"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Incorrect email or password" in data["message"]


def test_login_inactive_account(client, auth_mocks):
    """Test login with inactive account"""
    mock_user_service, _, _, _ = auth_mocks
    user = _make_user(email_verified=True, is_active=False)
    
    mock_user_service.get_user_by_email.return_value = user
    mock_user_service.verify_password.return_value = True

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "rahul@example.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "inactive" in data["message"].lower()


def test_login_unverified_account(client, auth_mocks):
    """Test login with unverified account"""
    mock_user_service, _, _, _ = auth_mocks
    user = _make_user(email_verified=False, is_active=True)
    
    mock_user_service.get_user_by_email.return_value = user
    mock_user_service.verify_password.return_value = True

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "rahul@example.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "not verified" in data["message"].lower()


def test_refresh_success(client, auth_mocks):
    """Test successful token refresh flow"""
    mock_user_service, _, _, mock_auth_service = auth_mocks
    user = _make_user(email_verified=True, is_active=True)
    
    mock_auth_service.hash_token.return_value = "hashed_refresh"
    
    refresh_token_record = RefreshTokenInDB(
        id="507f1f77bcf86cd799439013",
        user_id=user.id,
        token_hash="hashed_refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_auth_service.refresh_token_repository.get_by_token_hash.return_value = refresh_token_record
    mock_user_service.get_user_by_id.return_value = user
    mock_auth_service.create_access_token.return_value = "new_access_token"

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "test_refresh_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["access_token"] == "new_access_token"


def test_refresh_revoked(client, auth_mocks):
    """Test token refresh with a revoked token"""
    _, _, _, mock_auth_service = auth_mocks
    
    mock_auth_service.hash_token.return_value = "hashed_refresh"
    
    refresh_token_record = RefreshTokenInDB(
        id="507f1f77bcf86cd799439013",
        user_id="507f1f77bcf86cd799439011",
        token_hash="hashed_refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_auth_service.refresh_token_repository.get_by_token_hash.return_value = refresh_token_record

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "revoked_token"}
    )

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "revoked" in data["message"].lower()


def test_logout_success(client, auth_mocks):
    """Test successful logout flow"""
    _, _, _, mock_auth_service = auth_mocks
    
    mock_auth_service.hash_token.return_value = "hashed_refresh"
    mock_auth_service.refresh_token_repository.revoke_by_hash.return_value = True

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "test_refresh_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Logged out" in data["message"]


def test_me_endpoint_success(client, mocks):
    """Test retrieving authenticated current user profile"""
    user = _make_user(email_verified=True, is_active=True)
    
    # Directly override get_current_user dependency
    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer fake_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == user.email
    assert data["data"]["full_name"] == user.full_name


def test_forgot_password_success(client, mocks):
    """Test forgot password flow for registered email"""
    mock_user_service, mock_otp_service, mock_email_service = mocks
    user = _make_user(email_verified=True, is_active=True)
    
    mock_user_service.get_user_by_email.return_value = user
    mock_otp_service.send_otp.return_value = "123456"
    mock_email_service.send_password_reset_email.return_value = True

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "rahul@example.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "If this email is registered" in data["message"]
    
    mock_user_service.get_user_by_email.assert_called_once_with("rahul@example.com")
    mock_otp_service.send_otp.assert_called_once_with("rahul@example.com", OTPPurpose.PASSWORD_RESET)
    mock_email_service.send_password_reset_email.assert_called_once_with("rahul@example.com", "123456")


def test_forgot_password_unknown_email(client, mocks):
    """Test forgot password flow for unknown email (prevent enumeration)"""
    mock_user_service, mock_otp_service, mock_email_service = mocks
    mock_user_service.get_user_by_email.return_value = None

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "unknown@example.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "If this email is registered" in data["message"]
    
    mock_user_service.get_user_by_email.assert_called_once_with("unknown@example.com")
    mock_otp_service.send_otp.assert_not_called()
    mock_email_service.send_password_reset_email.assert_not_called()


def test_reset_password_success(client, auth_mocks):
    """Test successful password reset flow"""
    mock_user_service, mock_otp_service, _, mock_auth_service = auth_mocks
    user = _make_user(email_verified=True, is_active=True)
    otp_record = _make_otp(otp="123456")
    otp_record.purpose = OTPPurpose.PASSWORD_RESET
    
    # Mock find_one for latest OTP document
    mock_otp_service.otp_repository.collection.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439012",
        "email": "rahul@example.com",
        "otp": "123456",
        "purpose": "password_reset",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "verified": False,
        "created_at": datetime.now(timezone.utc)
    }
    mock_user_service.get_user_by_email.return_value = user
    mock_otp_service.verify_otp.return_value = otp_record
    mock_user_service.reset_password.return_value = True
    mock_auth_service.logout_all.return_value = 1

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "rahul@example.com",
            "otp": "123456",
            "new_password": "NewPassword123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "reset successfully" in data["message"]
    
    mock_user_service.reset_password.assert_called_once_with(user.id, "NewPassword123")
    mock_auth_service.logout_all.assert_called_once_with(user.id)


def test_reset_password_invalid_otp(client, auth_mocks):
    """Test password reset with mismatched OTP"""
    mock_user_service, mock_otp_service, _, _ = auth_mocks
    
    mock_otp_service.otp_repository.collection.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439012",
        "email": "rahul@example.com",
        "otp": "123456",
        "purpose": "password_reset",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "verified": False,
        "created_at": datetime.now(timezone.utc)
    }

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "rahul@example.com",
            "otp": "999999", # Mismatched OTP
            "new_password": "NewPassword123"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Invalid OTP" in data["message"]


def test_reset_password_expired_otp(client, auth_mocks):
    """Test password reset with expired OTP"""
    mock_user_service, mock_otp_service, _, _ = auth_mocks
    
    mock_otp_service.otp_repository.collection.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439012",
        "email": "rahul@example.com",
        "otp": "123456",
        "purpose": "password_reset",
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1), # Expired
        "verified": False,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=11)
    }

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "rahul@example.com",
            "otp": "123456",
            "new_password": "NewPassword123"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Expired OTP" in data["message"]


def test_reset_password_reused_otp(client, auth_mocks):
    """Test password reset with already verified OTP"""
    mock_user_service, mock_otp_service, _, _ = auth_mocks
    
    mock_otp_service.otp_repository.collection.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439012",
        "email": "rahul@example.com",
        "otp": "123456",
        "purpose": "password_reset",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "verified": True, # Already used
        "created_at": datetime.now(timezone.utc)
    }

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "rahul@example.com",
            "otp": "123456",
            "new_password": "NewPassword123"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "already been verified" in data["message"]


def test_reset_password_weak_password(client, auth_mocks):
    """Test password reset with weak password"""
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "rahul@example.com",
            "otp": "123456",
            "new_password": "weak" # Weak password
        }
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "Validation failed" in data["message"]


def test_google_login_new_user(client, auth_mocks):
    """Test successful Google login for a new user"""
    mock_user_service, _, _, mock_auth_service = auth_mocks
    
    # User does not exist yet
    mock_user_service.get_user_by_email.return_value = None
    
    mock_user = _make_user(email="google_user@example.com", email_verified=True, is_active=True)
    mock_user.auth_provider = AuthProvider.GOOGLE
    mock_user_service.create_oauth_user.return_value = mock_user
    
    token_response = TokenResponse(
        access_token="google_access_token",
        refresh_token="google_refresh_token",
        token_type="bearer",
        expires_in=1800,
        user=TokenUser(
            id=mock_user.id,
            role=mock_user.role,
            email=mock_user.email,
            full_name=mock_user.full_name,
            email_verified=mock_user.email_verified
        )
    )
    refresh_token_create = RefreshTokenCreate(
        user_id=mock_user.id,
        token_hash="hashed_refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False
    )
    mock_auth_service._build_token_pair.return_value = (token_response, "google_refresh_token", refresh_token_create)
    mock_auth_service.refresh_token_repository.create_token.return_value = MagicMock()

    mock_id_info = {
        "iss": "https://accounts.google.com",
        "sub": "google123",
        "email": "google_user@example.com",
        "email_verified": True,
        "name": "Google User",
        "picture": "http://example.com/pic.jpg",
        "aud": "mock_client_id"
    }

    with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_id_info):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "valid_token"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["access_token"] == "google_access_token"
    assert data["data"]["user"]["id"] == mock_user.id
    assert data["data"]["user"]["role"] == "patient"
    
    mock_user_service.get_user_by_email.assert_called_once_with("google_user@example.com")
    mock_user_service.create_oauth_user.assert_called_once_with(
        email="google_user@example.com",
        full_name="Google User",
        profile_picture="http://example.com/pic.jpg",
        provider=AuthProvider.GOOGLE
    )


def test_google_login_existing_user(client, auth_mocks):
    """Test Google login for an existing user"""
    mock_user_service, _, _, mock_auth_service = auth_mocks
    
    # User already exists
    user = _make_user(email="google_user@example.com", email_verified=False, is_active=False)
    mock_user_service.get_user_by_email.return_value = user
    
    # Setup updated user mocks
    mock_user_service.verify_user_email.return_value = user
    mock_user_service.update_user.return_value = user
    mock_user_service.get_user_by_id.return_value = user
    
    token_response = TokenResponse(
        access_token="google_access_token",
        refresh_token="google_refresh_token",
        token_type="bearer",
        expires_in=1800,
        user=TokenUser(
            id=user.id,
            role=user.role,
            email=user.email,
            full_name=user.full_name,
            email_verified=True
        )
    )
    refresh_token_create = RefreshTokenCreate(
        user_id=user.id,
        token_hash="hashed_refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False
    )
    mock_auth_service._build_token_pair.return_value = (token_response, "google_refresh_token", refresh_token_create)

    mock_id_info = {
        "iss": "https://accounts.google.com",
        "sub": "google123",
        "email": "google_user@example.com",
        "email_verified": True,
        "name": "Google User",
        "picture": "http://example.com/pic.jpg",
        "aud": "mock_client_id"
    }

    with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_id_info):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "valid_token"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["access_token"] == "google_access_token"
    
    mock_user_service.get_user_by_email.assert_called_once_with("google_user@example.com")
    mock_user_service.verify_user_email.assert_called_once_with(user.id)
    mock_user_service.update_user.assert_called_once()


def test_google_login_invalid_token(client, auth_mocks):
    """Test Google login with an invalid token"""
    with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("Token expired")):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "invalid_token"}
        )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Invalid Google token" in data["message"]


def test_google_login_invalid_issuer(client, auth_mocks):
    """Test Google login with a mismatched token issuer"""
    mock_id_info = {
        "iss": "hacker.com", # Mismatched issuer
        "sub": "google123",
        "email": "google_user@example.com",
        "email_verified": True,
        "name": "Google User",
        "aud": "mock_client_id"
    }

    with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_id_info):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "valid_token"}
        )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Invalid Google token" in data["message"]


def test_google_login_unverified_email(client, auth_mocks):
    """Test Google login with an unverified email address"""
    mock_id_info = {
        "iss": "https://accounts.google.com",
        "sub": "google123",
        "email": "google_user@example.com",
        "email_verified": False, # Email unverified in Google
        "name": "Google User",
        "aud": "mock_client_id"
    }

    with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_id_info):
        response = client.post(
            "/api/v1/auth/google",
            json={"id_token": "valid_token"}
        )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Google email is not verified" in data["message"]

