"""
Nura - Models Unit Tests
Tests for Pydantic v2 models: validation, normalization, enums.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from app.models import (
    UserRole,
    AuthProvider,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse,
    RefreshTokenCreate,
    RefreshTokenInDB,
    OTPPurpose,
    OTPVerificationCreate,
    OTPVerificationInDB,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# UserRole / AuthProvider enums
# ---------------------------------------------------------------------------

class TestEnums:
    def test_user_roles(self):
        assert UserRole.PATIENT.value == "patient"
        assert UserRole.DOCTOR.value == "doctor"
        assert UserRole.ADMIN.value == "admin"

    def test_auth_providers(self):
        assert AuthProvider.LOCAL.value == "local"
        assert AuthProvider.GOOGLE.value == "google"

    def test_otp_purposes(self):
        assert OTPPurpose.REGISTRATION.value == "registration"
        assert OTPPurpose.PASSWORD_RESET.value == "password_reset"


# ---------------------------------------------------------------------------
# UserCreate
# ---------------------------------------------------------------------------

class TestUserCreate:
    def test_valid(self):
        u = UserCreate(email="test@example.com", password="Password1", full_name="Alice")
        assert u.email == "test@example.com"
        assert u.role == UserRole.PATIENT
        assert u.auth_provider == AuthProvider.LOCAL
        assert u.email_verified is False
        assert u.is_active is True

    def test_email_normalised_to_lowercase(self):
        u = UserCreate(email="TEST@EXAMPLE.COM", password="Password1", full_name="Alice")
        assert u.email == "test@example.com"

    def test_email_whitespace_stripped(self):
        u = UserCreate(email="  user@example.com  ", password="Password1", full_name="Alice")
        assert u.email == "user@example.com"

    # --- password rules ---

    def test_password_too_short(self):
        with pytest.raises(ValidationError, match="8 characters"):
            UserCreate(email="a@b.com", password="Ab1", full_name="X")

    def test_password_missing_uppercase(self):
        with pytest.raises(ValidationError, match="uppercase"):
            UserCreate(email="a@b.com", password="password1", full_name="X")

    def test_password_missing_lowercase(self):
        with pytest.raises(ValidationError, match="lowercase"):
            UserCreate(email="a@b.com", password="PASSWORD1", full_name="X")

    def test_password_missing_digit(self):
        with pytest.raises(ValidationError, match="number"):
            UserCreate(email="a@b.com", password="Password", full_name="X")

    def test_password_exactly_8_chars_valid(self):
        u = UserCreate(email="a@b.com", password="Abcdef1!", full_name="X")
        assert len(u.password) == 8

    def test_invalid_email_format(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="Password1", full_name="X")


# ---------------------------------------------------------------------------
# UserUpdate
# ---------------------------------------------------------------------------

class TestUserUpdate:
    def test_all_optional(self):
        u = UserUpdate()
        assert u.full_name is None
        assert u.phone is None
        assert u.profile_picture is None
        assert u.is_active is None

    def test_partial_update(self):
        u = UserUpdate(full_name="Bob", is_active=False)
        assert u.full_name == "Bob"
        assert u.is_active is False


# ---------------------------------------------------------------------------
# UserInDB
# ---------------------------------------------------------------------------

class TestUserInDB:
    def test_direct_construction(self):
        now = utc_now()
        u = UserInDB(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            password_hash="$2b$hashed",
            full_name="Alice",
            role=UserRole.PATIENT,
            auth_provider=AuthProvider.LOCAL,
            email_verified=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert u.id == "507f1f77bcf86cd799439011"
        assert u.password_hash == "$2b$hashed"

    def test_from_mongo_converts_object_id(self):
        from bson import ObjectId
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "test@example.com",
            "password_hash": "$2b$hashed",
            "full_name": "Alice",
            "role": "patient",
            "auth_provider": "local",
            "email_verified": False,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        u = UserInDB.from_mongo(raw)
        assert u.id == "507f1f77bcf86cd799439011"
        assert isinstance(u.id, str)

    def test_from_mongo_does_not_mutate_input(self):
        from bson import ObjectId
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "x@x.com",
            "password_hash": "h",
            "full_name": "X",
            "role": "patient",
            "auth_provider": "local",
            "email_verified": False,
            "is_active": True,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        original_keys = set(raw.keys())
        UserInDB.from_mongo(raw)
        assert set(raw.keys()) == original_keys  # original dict untouched


# ---------------------------------------------------------------------------
# UserResponse
# ---------------------------------------------------------------------------

class TestUserResponse:
    def test_valid(self):
        now = utc_now()
        r = UserResponse(
            id="abc123",
            role=UserRole.DOCTOR,
            email="doc@hospital.com",
            full_name="Dr. Who",
            auth_provider=AuthProvider.LOCAL,
            email_verified=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert r.id == "abc123"
        assert r.role == UserRole.DOCTOR


# ---------------------------------------------------------------------------
# RefreshToken models
# ---------------------------------------------------------------------------

class TestRefreshTokenModels:
    def test_create_valid(self):
        expires = utc_now() + timedelta(days=7)
        t = RefreshTokenCreate(
            user_id="uid1",
            token_hash="hash",
            expires_at=expires,
            revoked=False,
        )
        assert t.revoked is False
        assert t.expires_at == expires

    def test_in_db_from_mongo(self):
        from bson import ObjectId
        expires = utc_now() + timedelta(days=7)
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "user_id": "uid1",
            "token_hash": "hash",
            "expires_at": expires,
            "revoked": False,
            "created_at": utc_now(),
        }
        t = RefreshTokenInDB.from_mongo(raw)
        assert t.id == "507f1f77bcf86cd799439012"
        assert isinstance(t.id, str)

    def test_default_revoked_is_false(self):
        t = RefreshTokenCreate(
            user_id="u",
            token_hash="h",
            expires_at=utc_now() + timedelta(days=1),
        )
        assert t.revoked is False


# ---------------------------------------------------------------------------
# OTPVerification models
# ---------------------------------------------------------------------------

class TestOTPVerificationModels:
    def test_create_valid(self):
        expires = utc_now() + timedelta(minutes=10)
        o = OTPVerificationCreate(
            email="test@example.com",
            otp="123456",
            purpose=OTPPurpose.REGISTRATION,
            expires_at=expires,
        )
        assert o.otp == "123456"
        assert o.verified is False

    def test_email_normalised(self):
        o = OTPVerificationCreate(
            email="UPPER@EXAMPLE.COM",
            otp="000000",
            purpose=OTPPurpose.PASSWORD_RESET,
            expires_at=utc_now() + timedelta(minutes=5),
        )
        assert o.email == "upper@example.com"

    def test_otp_too_short(self):
        with pytest.raises(ValidationError):
            OTPVerificationCreate(
                email="a@b.com",
                otp="12345",   # 5 chars
                purpose=OTPPurpose.REGISTRATION,
                expires_at=utc_now() + timedelta(minutes=5),
            )

    def test_otp_too_long(self):
        with pytest.raises(ValidationError):
            OTPVerificationCreate(
                email="a@b.com",
                otp="1234567",  # 7 chars
                purpose=OTPPurpose.REGISTRATION,
                expires_at=utc_now() + timedelta(minutes=5),
            )

    def test_in_db_from_mongo(self):
        from bson import ObjectId
        expires = utc_now() + timedelta(minutes=10)
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "email": "test@example.com",
            "otp": "654321",
            "purpose": "registration",
            "expires_at": expires,
            "verified": False,
            "created_at": utc_now(),
        }
        o = OTPVerificationInDB.from_mongo(raw)
        assert o.id == "507f1f77bcf86cd799439013"
        assert isinstance(o.id, str)
