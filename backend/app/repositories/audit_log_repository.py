"""
Nura - Audit Log Repository
MongoDB repository for audit_logs collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.observability import AuditLogCreate, AuditLogUpdate, AuditLogInDB
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLogInDB, AuditLogCreate, AuditLogUpdate]):
    """Repository for audit_logs collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, AuditLogInDB)

    async def get_by_id(self, id: str) -> Optional[AuditLogInDB]:
        """Fetch an audit log record by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[AuditLogInDB]:
        """List all audit log records"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_user(self, user_id: str, limit: int = 100, skip: int = 0) -> List[AuditLogInDB]:
        """Fetch audit logs executed by a specific user"""
        return await self.get_many({"user_id": user_id}, limit=limit, skip=skip)

    async def get_by_resource(self, resource_type: str, resource_id: Optional[str] = None, limit: int = 100, skip: int = 0) -> List[AuditLogInDB]:
        """Fetch audit logs affecting a specific resource type and optional resource ID"""
        query = {"resource_type": resource_type}
        if resource_id:
            query["resource_id"] = resource_id
        return await self.get_many(query, limit=limit, skip=skip)
