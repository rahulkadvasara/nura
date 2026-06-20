"""
Nura - Services Unit Tests
Business-logic tests — all external I/O is mocked.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from jose import jwt

from app.models import UserCreate, UserUpdate, UserInDB, UserRole, AuthProvider, OTPPurpose
from app.services import UserService, AuthService, OTPService
from app.repositories import UserRepository, RefreshTokenRepository, OTPRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _make_user(
    oid: str = "507f1f77bcf86cd799439011",
    email: str = "user@example.com",
    role: UserRole = UserRole.PATIENT,
    is_active: bool = True,
    email_verified: bool = True,
    password_hash: str = "placeholder",
) -> UserInDB:
    now = utc_now()
    return UserInDB(
        id=oid,
        email=email,
        password_hash=password_hash,
        full_name="Test User",
        role=role,
        auth_provider=AuthProvider.LOCAL,
        email_verified=email_verified,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


# ────────────────────────────────────────────────────────────────────────────
# UserService
# ────────────────────────────────────────────────────────────────────────────

class TestUserServicePasswords:
    """Password hashing helpers are pure functions — no mocks needed."""

    @pytest.fixture
    def svc(self) -> UserService:
        return UserService(AsyncMock(spec=UserRepository))

    def test_hash_produces_different_string(self, svc):
        h = svc.hash_password("Secret1!")
        assert h != "Secret1!"
        assert len(h) > 20

    def test_verify_correct_password(self, svc):
        h = svc.hash_password("Secret1!")
        assert svc.verify_password("Secret1!", h) is True

    def test_verify_wrong_password(self, svc):
        h = svc.hash_password("Secret1!")
        assert svc.verify_password("wrong", h) is False

    def test_two_hashes_of_same_password_differ(self, svc):
        """bcrypt uses random salts — same input, different hash."""
        h1 = svc.hash_password("Secret1!")
        h2 = svc.hash_password("Secret1!")
        assert h1 != h2
        # But both should verify
        assert svc.verify_password("Secret1!", h1)
        assert svc.verify_password("Secret1!", h2)


class TestUserServiceCRUD:

    @pytest.fixture
    def col(self) -> MagicMock:
        """Motor collection mock — mirrors the pattern in test_repositories.py."""
        c = MagicMock()
        c.find_one = AsyncMock()
        c.insert_one = AsyncMock()
        c.update_one = AsyncMock()
        c.update_many = AsyncMock()
        c.delete_many = AsyncMock()
        c.count_documents = AsyncMock()
        return c

    @pytest.fixture
    def repo(self, col) -> UserRepository:
        return UserRepository(col)

    @pytest.fixture
    def svc(self, repo):
        return UserService(repo)

    # create_user ─────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_create_user_success(self, svc, col):
        from bson import ObjectId
        from unittest.mock import MagicMock

        # exists_by_email → count_documents returns 0 (no existing user)
        col.count_documents.return_value = 0

        insert_result = MagicMock()
        insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
        col.insert_one.return_value = insert_result

        now = datetime.now(timezone.utc)
        col.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "user@example.com",
            "full_name": "Alice",
            "role": "patient",
            "password_hash": "hashed",
            "auth_provider": "local",
            "email_verified": False,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        result = await svc.create_user(
            UserCreate(email="user@example.com", password="Password1", full_name="Alice")
        )
        assert isinstance(result, UserInDB)
        assert result.email == "user@example.com"
        col.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_email_taken(self, svc, col):
        col.count_documents.return_value = 1

        with pytest.raises(ValueError, match="already exists"):
            await svc.create_user(
                UserCreate(email="taken@example.com", password="Password1", full_name="X")
            )
        col.insert_one.assert_not_called()

    # authenticate_user ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_authenticate_success(self, svc, col):
        user = _make_user(password_hash=svc.hash_password("Pass1word"))
        # get_by_email calls find_one on the collection
        col.find_one.return_value = {
            "_id": __import__("bson").ObjectId(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "password_hash": user.password_hash,
            "auth_provider": user.auth_provider.value,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        result = await svc.authenticate_user("user@example.com", "Pass1word")
        assert isinstance(result, UserInDB)
        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, svc, col):
        user = _make_user(password_hash=svc.hash_password("Correct1"))
        col.find_one.return_value = {
            "_id": __import__("bson").ObjectId(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "password_hash": user.password_hash,
            "auth_provider": user.auth_provider.value,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        result = await svc.authenticate_user("user@example.com", "Wrong1")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, svc, col):
        col.find_one.return_value = None
        result = await svc.authenticate_user("nobody@example.com", "Pass1word")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, svc, col):
        user = _make_user(is_active=False, password_hash=svc.hash_password("Pass1word"))
        col.find_one.return_value = {
            "_id": __import__("bson").ObjectId(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "password_hash": user.password_hash,
            "auth_provider": user.auth_provider.value,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        result = await svc.authenticate_user("user@example.com", "Pass1word")
        assert result is None

    # to_response ─────────────────────────────────────────────────────────

    def test_to_response_omits_password_hash(self, svc):
        user = _make_user(password_hash="secret_hash")
        response = svc.to_response(user)
        assert not hasattr(response, "password_hash")
        assert response.id == user.id
        assert response.email == user.email


# ────────────────────────────────────────────────────────────────────────────
# AuthService
# ────────────────────────────────────────────────────────────────────────────

class TestAuthServiceTokens:
    """Token creation / verification are pure — no async mocks needed."""

    @pytest.fixture
    def svc(self):
        return AuthService(
            user_service=AsyncMock(spec=UserService),
            refresh_token_repository=AsyncMock(spec=RefreshTokenRepository),
        )

    def test_create_access_token_decodable(self, svc):
        user = _make_user()
        token = svc.create_access_token(user)
        assert isinstance(token, str)

        from app.core.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == user.id
        assert payload["email"] == user.email
        assert payload["role"] == user.role.value
        assert payload["type"] == "access"

    def test_verify_access_token_valid(self, svc):
        user = _make_user()
        token = svc.create_access_token(user)
        payload = svc.verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == user.id

    def test_verify_access_token_invalid_string(self, svc):
        assert svc.verify_access_token("not.a.jwt") is None

    def test_verify_access_token_wrong_type(self, svc):
        """A token with type != 'access' must be rejected."""
        from app.core.config import settings
        from datetime import timedelta
        now = utc_now()
        payload = {
            "sub": "uid",
            "email": "e@e.com",
            "role": "patient",
            "iat": now,
            "exp": now + timedelta(minutes=30),
            "type": "refresh",       # wrong type
        }
        bad_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        assert svc.verify_access_token(bad_token) is None

    def test_create_refresh_token_length_and_expiry(self, svc):
        raw, expires_at = svc.create_refresh_token()
        assert len(raw) > 20
        assert expires_at > utc_now()

    def test_hash_and_verify_token(self, svc):
        raw = "some_opaque_token_string"
        hashed = svc.hash_token(raw)
        assert hashed != raw
        assert svc.verify_token_hash(raw, hashed) is True
        assert svc.verify_token_hash("other_token", hashed) is False


class TestAuthServiceLogin:

    @pytest.fixture
    def user_svc(self):
        return AsyncMock(spec=UserService)

    @pytest.fixture
    def token_repo(self):
        return AsyncMock(spec=RefreshTokenRepository)

    @pytest.fixture
    def svc(self, user_svc, token_repo):
        return AuthService(user_svc, token_repo)

    @pytest.mark.asyncio
    async def test_login_success(self, svc, user_svc):
        user = _make_user()
        user_svc.authenticate_user.return_value = user

        result = await svc.login("user@example.com", "Pass1word")
        assert result is not None
        token_response, refresh_create = result

        assert token_response.access_token
        assert token_response.refresh_token
        assert token_response.token_type == "bearer"
        assert token_response.expires_in > 0
        assert token_response.user.id == user.id

        assert refresh_create.user_id == user.id
        assert refresh_create.revoked is False
        assert refresh_create.expires_at > utc_now()

    @pytest.mark.asyncio
    async def test_login_wrong_credentials(self, svc, user_svc):
        user_svc.authenticate_user.return_value = None
        result = await svc.login("user@example.com", "Wrong")
        assert result is None


class TestAuthServiceRBAC:

    @pytest.fixture
    def svc(self):
        return AuthService(
            user_service=AsyncMock(spec=UserService),
            refresh_token_repository=AsyncMock(spec=RefreshTokenRepository),
        )

    def _user(self, role: UserRole) -> UserInDB:
        return _make_user(role=role)

    def test_admin_can_access_all_roles(self, svc):
        admin = self._user(UserRole.ADMIN)
        assert svc.has_role(admin, UserRole.ADMIN) is True
        assert svc.has_role(admin, UserRole.DOCTOR) is True
        assert svc.has_role(admin, UserRole.PATIENT) is True

    def test_doctor_can_access_doctor_and_patient(self, svc):
        doc = self._user(UserRole.DOCTOR)
        assert svc.has_role(doc, UserRole.ADMIN) is False
        assert svc.has_role(doc, UserRole.DOCTOR) is True
        assert svc.has_role(doc, UserRole.PATIENT) is True

    def test_patient_can_only_access_patient(self, svc):
        pat = self._user(UserRole.PATIENT)
        assert svc.has_role(pat, UserRole.ADMIN) is False
        assert svc.has_role(pat, UserRole.DOCTOR) is False
        assert svc.has_role(pat, UserRole.PATIENT) is True

    def test_require_role_raises_on_insufficient_role(self, svc):
        pat = self._user(UserRole.PATIENT)
        with pytest.raises(PermissionError):
            svc.require_role(pat, UserRole.DOCTOR)

    def test_require_role_passes_for_allowed_role(self, svc):
        admin = self._user(UserRole.ADMIN)
        svc.require_role(admin, UserRole.DOCTOR)  # should not raise


# ────────────────────────────────────────────────────────────────────────────
# OTPService
# ────────────────────────────────────────────────────────────────────────────

class TestOTPServiceGeneration:
    """Pure generation helpers — no repo needed."""

    @pytest.fixture
    def svc(self):
        return OTPService(AsyncMock(spec=OTPRepository))

    def test_generate_otp_is_numeric(self, svc):
        otp = svc.generate_otp(6)
        assert len(otp) == 6
        assert otp.isdigit()

    def test_generate_otp_custom_length(self, svc):
        assert len(svc.generate_otp(4)) == 4
        assert len(svc.generate_otp(8)) == 8

    def test_generate_otp_randomness(self, svc):
        """Two calls should (very likely) produce different values."""
        otps = {svc.generate_otp() for _ in range(20)}
        assert len(otps) > 1

    def test_calculate_expiry_in_future(self, svc):
        exp = svc.calculate_expiry(10)
        assert exp > utc_now()
        diff = exp - utc_now()
        assert timedelta(minutes=9, seconds=50) < diff < timedelta(minutes=10, seconds=10)

    def test_validate_email_format_valid(self, svc):
        assert svc.validate_email_format("a@b.com") is True
        assert svc.validate_email_format("user.name+tag@domain.co.uk") is True

    def test_validate_email_format_invalid(self, svc):
        assert svc.validate_email_format("") is False
        assert svc.validate_email_format("no-at-sign") is False
        assert svc.validate_email_format("@domain.com") is False
        assert svc.validate_email_format("user@") is False
        assert svc.validate_email_format("user@nodot") is False


class TestOTPServiceFlows:

    @pytest.fixture
    def repo(self):
        return AsyncMock(spec=OTPRepository)

    @pytest.fixture
    def svc(self, repo):
        return OTPService(repo)

    @pytest.mark.asyncio
    async def test_create_otp_returns_correct_fields(self, svc):
        raw, create = await svc.create_otp("user@example.com", OTPPurpose.REGISTRATION)
        assert raw.isdigit()
        assert len(raw) == 6
        assert create.otp == raw
        assert create.email == "user@example.com"
        assert create.purpose == OTPPurpose.REGISTRATION
        assert create.expires_at > utc_now()
        assert create.verified is False

    @pytest.mark.asyncio
    async def test_send_otp_calls_repo_in_order(self, svc, repo):
        repo.invalidate.return_value = 0
        repo.create_otp.return_value = MagicMock()

        raw = await svc.send_otp("user@example.com", OTPPurpose.REGISTRATION)
        assert isinstance(raw, str)
        assert raw.isdigit() and len(raw) == 6

        repo.invalidate.assert_called_once_with("user@example.com", OTPPurpose.REGISTRATION)
        repo.create_otp.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_otp_returns_none_on_error(self, svc, repo):
        repo.invalidate.side_effect = Exception("DB down")
        result = await svc.send_otp("user@example.com", OTPPurpose.REGISTRATION)
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_otp_delegates_to_repo(self, svc, repo):
        mock_otp = MagicMock()
        repo.verify_otp.return_value = mock_otp

        result = await svc.verify_otp("user@example.com", "123456", OTPPurpose.REGISTRATION)
        assert result is mock_otp
        repo.verify_otp.assert_called_once_with(
            "user@example.com", "123456", OTPPurpose.REGISTRATION
        )

    @pytest.mark.asyncio
    async def test_is_otp_valid_true(self, svc, repo):
        repo.verify_otp.return_value = MagicMock()
        assert await svc.is_otp_valid("u@e.com", "123456", OTPPurpose.REGISTRATION) is True

    @pytest.mark.asyncio
    async def test_is_otp_valid_false(self, svc, repo):
        repo.verify_otp.return_value = None
        assert await svc.is_otp_valid("u@e.com", "000000", OTPPurpose.REGISTRATION) is False

    @pytest.mark.asyncio
    async def test_rate_limit_check_below_limit(self, svc, repo):
        repo.get_many.return_value = [MagicMock(), MagicMock()]   # 2 < 3
        assert await svc.rate_limit_check("u@e.com", OTPPurpose.REGISTRATION) is True

    @pytest.mark.asyncio
    async def test_rate_limit_check_at_limit(self, svc, repo):
        repo.get_many.return_value = [MagicMock()] * 3            # 3 == limit
        assert await svc.rate_limit_check("u@e.com", OTPPurpose.REGISTRATION) is False

    @pytest.mark.asyncio
    async def test_rate_limit_passes_time_filter(self, svc, repo):
        repo.get_many.return_value = []
        await svc.rate_limit_check("u@e.com", OTPPurpose.REGISTRATION)

        call_filter = repo.get_many.call_args[0][0]
        assert call_filter["email"] == "u@e.com"
        assert call_filter["purpose"] == OTPPurpose.REGISTRATION
        assert "$gt" in call_filter["created_at"]
