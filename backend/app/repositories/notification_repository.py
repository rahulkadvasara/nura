"""
Nura - Notification Repository
MongoDB repository for notifications collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.notification import NotificationCreate, NotificationUpdate, NotificationInDB
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[NotificationInDB, NotificationCreate, NotificationUpdate]):
    """Repository for notifications collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, NotificationInDB)

    async def get_by_id(self, id: str) -> Optional[NotificationInDB]:
        """Fetch a notification by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[NotificationInDB]:
        """List all notifications"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_user_id(self, user_id: str, limit: int = 100, skip: int = 0) -> List[NotificationInDB]:
        """Fetch all notifications for a given user"""
        return await self.get_many({"user_id": user_id}, limit=limit, skip=skip)

    async def get_unread(self, user_id: str, limit: int = 100, skip: int = 0) -> List[NotificationInDB]:
        """Fetch all unread notifications for a given user"""
        return await self.get_many({"user_id": user_id, "read": False}, limit=limit, skip=skip)

    async def mark_as_read(self, id: str) -> Optional[NotificationInDB]:
        """Mark a specific notification as read"""
        return await self.update(id, NotificationUpdate(read=True))

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read. Returns the count of modified documents."""
        result = await self.collection.update_many(
            {"user_id": user_id, "read": False},
            {"$set": {"read": True}}
        )
        return result.modified_count
