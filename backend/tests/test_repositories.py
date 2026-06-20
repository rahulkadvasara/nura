"""
Nura - Repository Unit Tests
Pure unit tests — all MongoDB I/O is mocked via AsyncMock / MagicMock.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from app.models import (
    UserCreate,
    UserUpdate,
    UserInDB,
    RefreshTokenCreate,
    RefreshTokenInDB,
    OTPVerificationCreate,
    OTPVerificationInDB,
    UserRole,
    AuthProvider,
    OTPPurpose,
)
from app.repositories import UserRepository, RefreshTokenRepository, OTPRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _user_doc(oid_str: str = "507f1f77bcf86cd799439011") -> dict:
    return {
        "_id": ObjectId(oid_str),
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "patient",
        "password_hash": "$2b$hashed",
        "auth_provider": "local",
        "email_verified": False,
        "is_active": True,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def _token_doc(oid_str: str = "507f1f77bcf86cd799439011") -> dict:
    return {
        "_id": ObjectId(oid_str),
        "user_id": "user123",
        "token_hash": "test_hash",
        "expires_at": utc_now() + timedelta(days=1),
        "revoked": False,
        "created_at": utc_now(),
    }


def _otp_doc(oid_str: str = "507f1f77bcf86cd799439011") -> dict:
    return {
        "_id": ObjectId(oid_str),
        "email": "test@example.com",
        "otp": "123456",
        "purpose": "registration",
        "expires_at": utc_now() + timedelta(minutes=10),
        "verified": False,
        "created_at": utc_now(),
    }


def _mock_cursor(docs: list) -> AsyncMock:
    """Return an AsyncMock that behaves like a Motor cursor."""
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=docs)
    return cursor


# ────────────────────────────────────────────────────────────────────────────
# UserRepository
# ────────────────────────────────────────────────────────────────────────────

class TestUserRepository:

    @pytest.fixture
    def col(self) -> MagicMock:
        """Motor collection mock — find() is synchronous in Motor."""
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

    # get_by_email ──────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_by_email_found(self, repo, col):
        col.find_one.return_value = _user_doc()
        result = await repo.get_by_email("test@example.com")
        assert isinstance(result, UserInDB)
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.email == "test@example.com"
        col.find_one.assert_called_once_with({"email": "test@example.com"})

    @pytest.mark.asyncio
    async def test_get_by_email_uppercase_normalised(self, repo, col):
        col.find_one.return_value = None
        await repo.get_by_email("TEST@EXAMPLE.COM")
        col.find_one.assert_called_once_with({"email": "test@example.com"})

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, repo, col):
        col.find_one.return_value = None
        result = await repo.get_by_email("nobody@example.com")
        assert result is None

    # get_by_id ─────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, col):
        col.find_one.return_value = _user_doc()
        result = await repo.get_by_id("507f1f77bcf86cd799439011")
        assert isinstance(result, UserInDB)
        assert result.id == "507f1f77bcf86cd799439011"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo, col):
        col.find_one.return_value = None
        result = await repo.get_by_id("507f1f77bcf86cd799439011")
        assert result is None

    # verify_email ──────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_verify_email(self, repo, col):
        update_result = MagicMock()
        update_result.modified_count = 1
        col.update_one.return_value = update_result

        doc = {**_user_doc(), "email_verified": True}
        col.find_one.return_value = doc

        result = await repo.verify_email("507f1f77bcf86cd799439011")
        assert isinstance(result, UserInDB)
        assert result.email_verified is True
        col.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_not_modified(self, repo, col):
        update_result = MagicMock()
        update_result.modified_count = 0
        col.update_one.return_value = update_result
        result = await repo.verify_email("507f1f77bcf86cd799439011")
        assert result is None

    # exists_by_email ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_exists_by_email_true(self, repo, col):
        col.count_documents.return_value = 1
        assert await repo.exists_by_email("test@example.com") is True
        col.count_documents.assert_called_once_with({"email": "test@example.com"}, limit=1)

    @pytest.mark.asyncio
    async def test_exists_by_email_false(self, repo, col):
        col.count_documents.return_value = 0
        assert await repo.exists_by_email("no@example.com") is False

    # create_user ───────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_create_user(self, repo, col):
        insert_result = MagicMock()
        insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
        col.insert_one.return_value = insert_result

        doc = _user_doc()
        col.find_one.return_value = doc

        user_create = UserCreate(
            email="test@example.com",
            password="Password1",
            full_name="Test User",
        )
        result = await repo.create_user(user_create)
        assert isinstance(result, UserInDB)
        assert result.id == "507f1f77bcf86cd799439011"
        col.insert_one.assert_called_once()


# ────────────────────────────────────────────────────────────────────────────
# RefreshTokenRepository
# ────────────────────────────────────────────────────────────────────────────

class TestRefreshTokenRepository:

    @pytest.fixture
    def col(self) -> MagicMock:
        """Motor collection mock.

        Motor's find() is synchronous (returns a cursor), so the collection
        itself must be a MagicMock.  Individual async operations (find_one,
        insert_one, update_one, update_many, delete_many, count_documents)
        are patched as AsyncMocks so they can be awaited.
        """
        c = MagicMock()
        c.find_one = AsyncMock()
        c.insert_one = AsyncMock()
        c.update_one = AsyncMock()
        c.update_many = AsyncMock()
        c.delete_many = AsyncMock()
        c.count_documents = AsyncMock()
        return c

    @pytest.fixture
    def repo(self, col) -> RefreshTokenRepository:
        return RefreshTokenRepository(col)

    # revoke_user_tokens ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_revoke_user_tokens(self, repo, col):
        upd = MagicMock()
        upd.modified_count = 3
        col.update_many.return_value = upd

        count = await repo.revoke_user_tokens("user123")
        assert count == 3

        call_filter = col.update_many.call_args[0][0]
        assert call_filter["user_id"] == "user123"
        assert call_filter["revoked"] is False
        assert "$gt" in call_filter["expires_at"]

    # get_active ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_active(self, repo, col):
        docs = [
            {**_token_doc("507f1f77bcf86cd799439011"), "token_hash": "h1"},
            {**_token_doc("507f1f77bcf86cd799439012"), "token_hash": "h2"},
        ]
        col.find.return_value = _mock_cursor(docs)

        result = await repo.get_active("user123")
        assert len(result) == 2
        assert all(isinstance(t, RefreshTokenInDB) for t in result)
        assert result[0].revoked is False

    @pytest.mark.asyncio
    async def test_get_active_empty(self, repo, col):
        col.find.return_value = _mock_cursor([])
        result = await repo.get_active("user123")
        assert result == []

    # get_by_token_hash ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_by_token_hash_found(self, repo, col):
        col.find_one.return_value = _token_doc()
        result = await repo.get_by_token_hash("test_hash")
        assert isinstance(result, RefreshTokenInDB)
        assert result.token_hash == "test_hash"
        col.find_one.assert_called_once_with({"token_hash": "test_hash"})

    @pytest.mark.asyncio
    async def test_get_by_token_hash_not_found(self, repo, col):
        col.find_one.return_value = None
        result = await repo.get_by_token_hash("no_such_hash")
        assert result is None

    # cleanup_expired_tokens ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, repo, col):
        del_result = MagicMock()
        del_result.deleted_count = 5
        col.delete_many.return_value = del_result

        count = await repo.cleanup_expired_tokens()
        assert count == 5

        call_filter = col.delete_many.call_args[0][0]
        assert "$lt" in call_filter["expires_at"]


# ────────────────────────────────────────────────────────────────────────────
# OTPRepository
# ────────────────────────────────────────────────────────────────────────────

class TestOTPRepository:

    @pytest.fixture
    def col(self) -> MagicMock:
        """Motor collection mock — find() is synchronous in Motor."""
        c = MagicMock()
        c.find_one = AsyncMock()
        c.insert_one = AsyncMock()
        c.update_one = AsyncMock()
        c.update_many = AsyncMock()
        c.delete_many = AsyncMock()
        c.count_documents = AsyncMock()
        return c

    @pytest.fixture
    def repo(self, col) -> OTPRepository:
        return OTPRepository(col)

    # get_latest ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_latest_found(self, repo, col):
        col.find.return_value = _mock_cursor([_otp_doc()])
        result = await repo.get_latest("test@example.com", OTPPurpose.REGISTRATION)
        assert isinstance(result, OTPVerificationInDB)
        assert result.otp == "123456"
        assert result.purpose == OTPPurpose.REGISTRATION

    @pytest.mark.asyncio
    async def test_get_latest_not_found(self, repo, col):
        col.find.return_value = _mock_cursor([])
        result = await repo.get_latest("test@example.com", OTPPurpose.REGISTRATION)
        assert result is None

    # invalidate ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_invalidate(self, repo, col):
        upd = MagicMock()
        upd.modified_count = 2
        col.update_many.return_value = upd

        count = await repo.invalidate("test@example.com", OTPPurpose.REGISTRATION)
        assert count == 2

        call_filter = col.update_many.call_args[0][0]
        assert call_filter["email"] == "test@example.com"
        assert call_filter["purpose"] == OTPPurpose.REGISTRATION
        assert call_filter["verified"] is False

    # verify_otp ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_verify_otp_success(self, repo, col):
        doc = _otp_doc()
        col.find_one.return_value = doc

        upd = MagicMock()
        upd.modified_count = 1
        col.update_one.return_value = upd

        result = await repo.verify_otp("test@example.com", "123456", OTPPurpose.REGISTRATION)
        assert isinstance(result, OTPVerificationInDB)
        assert result.verified is True
        col.find_one.assert_called_once()
        col.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_otp_not_found(self, repo, col):
        col.find_one.return_value = None
        result = await repo.verify_otp("test@example.com", "000000", OTPPurpose.REGISTRATION)
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_otp_update_fails(self, repo, col):
        """update_one returns 0 modified — should return None."""
        col.find_one.return_value = _otp_doc()
        upd = MagicMock()
        upd.modified_count = 0
        col.update_one.return_value = upd
        result = await repo.verify_otp("test@example.com", "123456", OTPPurpose.REGISTRATION)
        assert result is None

    # cleanup_expired_otps ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_cleanup_expired_otps(self, repo, col):
        del_result = MagicMock()
        del_result.deleted_count = 3
        col.delete_many.return_value = del_result

        count = await repo.cleanup_expired_otps()
        assert count == 3

        call_filter = col.delete_many.call_args[0][0]
        assert "$lt" in call_filter["expires_at"]
