"""
Nura - Admin Bootstrap Unit Tests
Verifies config validation, seeding, idempotency, login, and recovery for admin bootstrap.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings
from app.models import UserCreate, UserInDB, UserRole, AuthProvider
from app.repositories import UserRepository, AuditLogRepository
from app.services import UserService, AdminBootstrapService, AuthService
from app.repositories.refresh_token_repository import RefreshTokenRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_user_col() -> MagicMock:
    col = MagicMock()
    col.find_one = AsyncMock()
    col.insert_one = AsyncMock()
    col.update_one = AsyncMock()
    col.count_documents = AsyncMock()
    return col


@pytest.fixture
def mock_user_repo(mock_user_col) -> UserRepository:
    return UserRepository(mock_user_col)


@pytest.fixture
def mock_audit_col() -> MagicMock:
    col = MagicMock()
    col.insert_one = AsyncMock()
    return col


@pytest.fixture
def mock_audit_repo(mock_audit_col) -> AuditLogRepository:
    return AuditLogRepository(mock_audit_col)


@pytest.fixture
def user_service(mock_user_repo) -> UserService:
    return UserService(mock_user_repo)


@pytest.fixture
def bootstrap_service(user_service, mock_audit_repo) -> AdminBootstrapService:
    return AdminBootstrapService(user_service, mock_audit_repo)


# ────────────────────────────────────────────────────────────────────────────
# Configuration Validation Tests
# ────────────────────────────────────────────────────────────────────────────

class TestAdminBootstrapValidation:

    def test_validate_config_disabled(self, bootstrap_service):
        with patch.object(settings, "ADMIN_EMAIL", ""), \
             patch.object(settings, "ADMIN_PASSWORD", ""), \
             patch.object(settings, "ADMIN_NAME", ""):
            assert bootstrap_service.validate_bootstrap_config() is False

    def test_validate_config_partial_missing_email(self, bootstrap_service):
        with patch.object(settings, "ADMIN_EMAIL", ""), \
             patch.object(settings, "ADMIN_PASSWORD", "Password123!"), \
             patch.object(settings, "ADMIN_NAME", "Admin Name"):
            with pytest.raises(ValueError, match="partially configured"):
                bootstrap_service.validate_bootstrap_config()

    def test_validate_config_partial_missing_password(self, bootstrap_service):
        with patch.object(settings, "ADMIN_EMAIL", "admin@nura.app"), \
             patch.object(settings, "ADMIN_PASSWORD", ""), \
             patch.object(settings, "ADMIN_NAME", "Admin Name"):
            with pytest.raises(ValueError, match="partially configured"):
                bootstrap_service.validate_bootstrap_config()

    def test_validate_config_partial_missing_name(self, bootstrap_service):
        with patch.object(settings, "ADMIN_EMAIL", "admin@nura.app"), \
             patch.object(settings, "ADMIN_PASSWORD", "Password123!"), \
             patch.object(settings, "ADMIN_NAME", ""):
            with pytest.raises(ValueError, match="partially configured"):
                bootstrap_service.validate_bootstrap_config()

    def test_validate_config_invalid_email(self, bootstrap_service):
        with patch.object(settings, "ADMIN_EMAIL", "invalid-email"), \
             patch.object(settings, "ADMIN_PASSWORD", "Password123!"), \
             patch.object(settings, "ADMIN_NAME", "Admin Name"):
            with pytest.raises(ValueError, match="invalid"):
                bootstrap_service.validate_bootstrap_config()

    def test_validate_config_weak_password(self, bootstrap_service):
        with patch.object(settings, "ADMIN_EMAIL", "admin@nura.app"), \
             patch.object(settings, "ADMIN_PASSWORD", "weak"), \
             patch.object(settings, "ADMIN_NAME", "Admin Name"):
            with pytest.raises(ValueError, match="invalid"):
                bootstrap_service.validate_bootstrap_config()

    def test_validate_config_valid(self, bootstrap_service):
        with patch.object(settings, "ADMIN_EMAIL", "admin@nura.app"), \
             patch.object(settings, "ADMIN_PASSWORD", "Password123!"), \
             patch.object(settings, "ADMIN_NAME", "Admin Name"):
            assert bootstrap_service.validate_bootstrap_config() is True


# ────────────────────────────────────────────────────────────────────────────
# Seeding and Idempotency Tests
# ────────────────────────────────────────────────────────────────────────────

class TestAdminBootstrapSeeding:

    @pytest.mark.asyncio
    async def test_bootstrap_admin_already_exists(self, bootstrap_service, mock_user_col):
        # count_documents returns 1 (admin exists)
        mock_user_col.count_documents.return_value = 1

        with patch.object(settings, "ADMIN_EMAIL", "admin@nura.app"), \
             patch.object(settings, "ADMIN_PASSWORD", "Password123!"), \
             patch.object(settings, "ADMIN_NAME", "Admin Name"):
            
            result = await bootstrap_service.bootstrap_admin()
            
            assert result is None
            mock_user_col.count_documents.assert_called_once_with({"role": UserRole.ADMIN}, limit=1)
            mock_user_col.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_bootstrap_admin_success(self, bootstrap_service, mock_user_col, mock_audit_col):
        # count_documents returns 0 (no admin exists, no email conflicts)
        mock_user_col.count_documents.return_value = 0

        from bson import ObjectId
        insert_result = MagicMock()
        insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439001")
        mock_user_col.insert_one.return_value = insert_result

        now = utc_now()
        mock_user_col.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439001"),
            "email": "admin@nura.app",
            "full_name": "Admin Name",
            "role": "admin",
            "password_hash": "hashed_pw",
            "auth_provider": "local",
            "email_verified": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }

        with patch.object(settings, "ADMIN_EMAIL", "admin@nura.app"), \
             patch.object(settings, "ADMIN_PASSWORD", "Password123!"), \
             patch.object(settings, "ADMIN_NAME", "Admin Name"):

            result_id = await bootstrap_service.bootstrap_admin()

            assert result_id == "507f1f77bcf86cd799439001"
            
            # Verify admin properties
            called_args = mock_user_col.insert_one.call_args[0][0]
            assert called_args["role"] == UserRole.ADMIN
            assert called_args["email_verified"] is True
            assert called_args["is_active"] is True
            assert called_args["email"] == "admin@nura.app"

            # Verify audit log insertion
            mock_audit_col.insert_one.assert_called_once()
            audit_args = mock_audit_col.insert_one.call_args[0][0]
            assert audit_args["action"] == "ADMIN_BOOTSTRAP_CREATED"
            assert audit_args["resource_type"] == "user"
            assert audit_args["resource_id"] == "507f1f77bcf86cd799439001"
            assert audit_args["new_value"]["email"] == "admin@nura.app"
            assert audit_args["new_value"]["creator"] == "system"

    @pytest.mark.asyncio
    async def test_bootstrap_admin_invalid_config_fails(self, bootstrap_service):
        with patch.object(settings, "ADMIN_EMAIL", "invalid-email"), \
             patch.object(settings, "ADMIN_PASSWORD", "Password123!"), \
             patch.object(settings, "ADMIN_NAME", "Admin Name"):
            
            with pytest.raises(ValueError, match="invalid"):
                await bootstrap_service.bootstrap_admin()


# ────────────────────────────────────────────────────────────────────────────
# Auth Integration Tests
# ────────────────────────────────────────────────────────────────────────────

class TestAdminAuthIntegration:

    @pytest.mark.asyncio
    async def test_admin_login_flow(self, user_service):
        hashed_pw = user_service.hash_password("Password123!")
        now = utc_now()
        admin_doc = {
            "_id": __import__("bson").ObjectId("507f1f77bcf86cd799439001"),
            "email": "admin@nura.app",
            "full_name": "Admin Name",
            "role": "admin",
            "password_hash": hashed_pw,
            "auth_provider": "local",
            "email_verified": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }

        # Mock collection find_one for authentication lookups
        user_service.user_repository.collection.find_one.return_value = admin_doc

        # Test authenticate_user
        authenticated_user = await user_service.authenticate_user("admin@nura.app", "Password123!")
        assert authenticated_user is not None
        assert authenticated_user.role == UserRole.ADMIN
        assert authenticated_user.email == "admin@nura.app"
        assert authenticated_user.is_active is True
        assert authenticated_user.email_verified is True

        # Test auth token generation
        auth_service = AuthService(user_service, AsyncMock(spec=RefreshTokenRepository))
        token_response, raw_refresh, refresh_create = await auth_service._build_token_pair(authenticated_user)
        assert token_response.access_token
        assert token_response.user.role == UserRole.ADMIN
        assert token_response.user.email == "admin@nura.app"

    @pytest.mark.asyncio
    async def test_admin_password_recovery(self, user_service):
        hashed_pw = user_service.hash_password("Password123!")
        now = utc_now()
        admin_doc = {
            "_id": __import__("bson").ObjectId("507f1f77bcf86cd799439001"),
            "email": "admin@nura.app",
            "full_name": "Admin Name",
            "role": "admin",
            "password_hash": hashed_pw,
            "auth_provider": "local",
            "email_verified": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }

        # Mock user repo update
        user_service.user_repository.collection.find_one.return_value = admin_doc
        user_service.user_repository.update = AsyncMock(return_value=UserInDB.from_mongo(admin_doc))

        # Reset password unconditionally
        res = await user_service.reset_password("507f1f77bcf86cd799439001", "NewPassword123!")
        assert res is True
        
        # Verify update was called
        user_service.user_repository.update.assert_called_once()
        update_arg = user_service.user_repository.update.call_args[0][1]
        assert update_arg.password_hash is not None
        assert user_service.verify_password("NewPassword123!", update_arg.password_hash)
