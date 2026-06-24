"""
Nura - Admin Bootstrap Service
Business logic for platform initialization and admin seeding on startup
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.models import UserCreate, UserRole, AuthProvider
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class AdminBootstrapService:
    """Manages the verification and automated seeding of the first admin account."""

    def __init__(self, user_service: UserService, audit_log_repository: AuditLogRepository):
        self.user_service = user_service
        self.audit_log_repository = audit_log_repository

    def validate_bootstrap_config(self) -> bool:
        """Validate admin bootstrap environment variables.

        Returns:
            bool: True if bootstrap is enabled and configuration is valid.
                  False if bootstrap is not configured (disabled).

        Raises:
            ValueError: If bootstrap is enabled but configuration is invalid or partial.
        """
        email = settings.ADMIN_EMAIL
        password = settings.ADMIN_PASSWORD
        name = settings.ADMIN_NAME

        # If all variables are empty, bootstrap is not enabled
        if not email and not password and not name:
            logger.info("Admin bootstrap configuration is empty. Seeding skipped.")
            return False

        # If some variables are set but not all, it's partially configured
        if not email or not password or not name:
            error_msg = (
                "Admin bootstrap is partially configured. "
                "All of ADMIN_EMAIL, ADMIN_PASSWORD, and ADMIN_NAME must be provided."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate format using UserCreate validator (covers email format and password strength)
        try:
            UserCreate(
                email=email,
                password=password,
                full_name=name,
                role=UserRole.ADMIN,
                email_verified=True,
                is_active=True
            )
        except Exception as e:
            error_msg = f"Admin bootstrap configuration is invalid: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        return True

    async def bootstrap_admin(self) -> Optional[str]:
        """Bootstrap the first administrator.

        This checks if an admin exists, and if not, creates the first admin account.
        This operation is idempotent.

        Returns:
            Optional[str]: Created Admin User ID if bootstrap occurred, else None.
        """
        # Validate configuration. If disabled, exit early.
        if not self.validate_bootstrap_config():
            return None

        # Check if any admin exists in the database
        admin_exists = await self.user_service.user_repository.exists({"role": UserRole.ADMIN})
        if admin_exists:
            logger.info("An administrator account already exists. Skipping bootstrap seeding.")
            return None

        logger.info(f"No administrator found. Seeding first admin: {settings.ADMIN_EMAIL}")

        # Create user
        user_create = UserCreate(
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            full_name=settings.ADMIN_NAME,
            role=UserRole.ADMIN,
            email_verified=True,
            is_active=True
        )

        admin_user = await self.user_service.create_user(user_create)

        # Log audit event ADMIN_BOOTSTRAP_CREATED
        now = datetime.now(timezone.utc)
        audit_log = {
            "user_id": None,
            "action": "ADMIN_BOOTSTRAP_CREATED",
            "resource_type": "user",
            "resource_id": admin_user.id,
            "old_value": None,
            "new_value": {
                "email": admin_user.email,
                "creator": "system"
            },
            "ip_address": None,
            "user_agent": None,
            "created_at": now
        }

        await self.audit_log_repository.collection.insert_one(audit_log)
        logger.info(f"Successfully bootstrapped first administrator: {admin_user.email} (ID: {admin_user.id})")
        return admin_user.id
