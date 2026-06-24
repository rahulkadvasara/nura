"""
Nura - Audit Log Service
Business logic and operations for audit trail logging
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.observability import (
    AuditLogCreate,
    AuditLogUpdate,
    AuditLogInDB,
)
from app.schemas.observability import (
    AuditLogCreateSchema,
    AuditLogUpdateSchema,
    AuditLogResponse,
)
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _log_to_response(log: AuditLogInDB) -> AuditLogResponse:
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
        created_at=log.created_at,
    )


class AuditLogService(BaseService[AuditLogInDB, AuditLogCreate, AuditLogUpdate]):
    """Service layer for audit log operations"""

    def __init__(
        self,
        audit_log_repository: AuditLogRepository,
        user_repository: UserRepository,
    ):
        super().__init__()
        self.audit_log_repository = audit_log_repository
        self.user_repository = user_repository

    async def create_log(
        self,
        schema: AuditLogCreateSchema,
    ) -> AuditLogInDB:
        """Create a new audit log record after validating user existence (if user_id is provided)"""
        # Validate user exists (if user_id provided)
        if schema.user_id:
            user = await self.user_repository.get(schema.user_id)
            if not user:
                raise ValueError(f"User with ID {schema.user_id} does not exist")

        now = utc_now()
        audit_create = AuditLogCreate(
            user_id=schema.user_id,
            action=schema.action,
            resource_type=schema.resource_type,
            resource_id=schema.resource_id,
            old_value=schema.old_value,
            new_value=schema.new_value,
            ip_address=schema.ip_address,
            user_agent=schema.user_agent,
        )

        doc_dict = audit_create.model_dump()
        doc_dict["created_at"] = now

        result = await self.audit_log_repository.collection.insert_one(doc_dict)
        created = await self.audit_log_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Audit log was inserted but could not be retrieved")
        return AuditLogInDB.from_mongo(created)

    async def get_log_by_id(self, log_id: str) -> Optional[AuditLogInDB]:
        """Fetch an audit log by its ID"""
        return await self.audit_log_repository.get(log_id)

    async def list_logs(self, limit: int = 100, skip: int = 0) -> List[AuditLogInDB]:
        """List all audit logs"""
        return await self.audit_log_repository.list(limit=limit, skip=skip)

    async def list_logs_by_user(
        self,
        user_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[AuditLogInDB]:
        """Fetch audit logs for a user"""
        return await self.audit_log_repository.get_by_user(user_id, limit=limit, skip=skip)

    async def list_logs_by_resource(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[AuditLogInDB]:
        """Fetch audit logs for a target resource type and optional ID"""
        return await self.audit_log_repository.get_by_resource(resource_type, resource_id=resource_id, limit=limit, skip=skip)

    def to_response(self, log: AuditLogInDB) -> AuditLogResponse:
        """Convert internal model to API response"""
        return _log_to_response(log)

    async def get_admin_audit_logs(
        self,
        admin_id: str,
        limit: int = 50,
    ) -> List[AuditLogInDB]:
        """Fetch audit logs where the admin is the actor or the target, sorted newest first"""
        return await self.audit_log_repository.get_admin_audit_logs(admin_id, limit)

