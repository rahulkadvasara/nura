"""
Nura - Auth API Integration Tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from app.main import app
from app.core.dependencies import get_user_service, get_otp_service, get_email_service
from app.models import UserInDB, UserRole, AuthProvider, OTPVerificationInDB, OTPPurpose


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
