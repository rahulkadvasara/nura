"""
Nura - Maintenance Service
Handles database cleanup operations, purging expired records, and archiving logs and notifications.
"""

from datetime import datetime, timezone, timedelta
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.otp_repository import OTPRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.audit_log_repository import AuditLogRepository


class MaintenanceService:
    """Service layer to run administrative maintenance and cleanups"""

    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        otp_repository: OTPRepository,
        notification_repository: NotificationRepository,
        audit_log_repository: AuditLogRepository,
    ):
        self.refresh_token_repository = refresh_token_repository
        self.otp_repository = otp_repository
        self.notification_repository = notification_repository
        self.audit_log_repository = audit_log_repository

    async def clear_expired_sessions(self) -> int:
        """Purge all expired refresh tokens from database"""
        return await self.refresh_token_repository.cleanup_expired_tokens()

    async def clear_expired_otps(self) -> int:
        """Purge all expired OTP records from database"""
        return await self.otp_repository.cleanup_expired_otps()

    async def archive_notifications(self, retention_days: int = 30) -> int:
        """Archive notifications older than configured retention period, moving them to backups"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        db = self.notification_repository.collection.database
        archive_collection = db["archived_notifications"]

        # Fetch old notification records
        cursor = self.notification_repository.collection.find({"created_at": {"$lt": cutoff_date}})
        docs = await cursor.to_list(length=None)
        if not docs:
            return 0

        # Bulk copy to archive collection
        await archive_collection.insert_many(docs)
        # Delete from active collection
        result = await self.notification_repository.collection.delete_many({"created_at": {"$lt": cutoff_date}})
        return result.deleted_count

    async def archive_audit_logs(self, retention_days: int = 90) -> int:
        """Archive audit log entries older than configured retention period, moving them to backups"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        db = self.audit_log_repository.collection.database
        archive_collection = db["archived_audit_logs"]

        # Fetch old audit trail entries
        cursor = self.audit_log_repository.collection.find({"created_at": {"$lt": cutoff_date}})
        docs = await cursor.to_list(length=None)
        if not docs:
            return 0

        # Bulk copy to archive collection
        await archive_collection.insert_many(docs)
        # Delete from active collection
        result = await self.audit_log_repository.collection.delete_many({"created_at": {"$lt": cutoff_date}})
        return result.deleted_count
