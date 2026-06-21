"""
Nura - Notification Service
Business logic and validation for user notifications
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationInDB,
    NotificationType,
    NotificationPriority,
)
from app.schemas.notification import (
    NotificationCreateSchema,
    NotificationUpdateSchema,
    NotificationResponse,
)
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _notification_to_response(notification: NotificationInDB) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        read=notification.read,
        priority=notification.priority,
        related_entity_type=notification.related_entity_type,
        related_entity_id=notification.related_entity_id,
        created_at=notification.created_at,
    )


class NotificationService(BaseService[NotificationInDB, NotificationCreate, NotificationUpdate]):
    """Service layer for user notification operations"""

    def __init__(
        self,
        notification_repository: NotificationRepository,
        user_repository: UserRepository,
    ):
        super().__init__()
        self.notification_repository = notification_repository
        self.user_repository = user_repository

    async def create_notification(
        self,
        schema: NotificationCreateSchema,
    ) -> NotificationInDB:
        """Create a new notification record after validating user existence"""
        # Validate user exists
        user = await self.user_repository.get(schema.user_id)
        if not user:
            raise ValueError(f"User with ID {schema.user_id} does not exist")

        now = utc_now()
        notification_create = NotificationCreate(
            user_id=schema.user_id,
            notification_type=schema.notification_type,
            title=schema.title,
            message=schema.message,
            read=schema.read,
            priority=schema.priority,
            related_entity_type=schema.related_entity_type,
            related_entity_id=schema.related_entity_id,
        )

        doc_dict = notification_create.model_dump()
        doc_dict["created_at"] = now

        result = await self.notification_repository.collection.insert_one(doc_dict)
        created = await self.notification_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Notification was inserted but could not be retrieved")
        return NotificationInDB.from_mongo(created)

    async def get_notification_by_id(self, notification_id: str) -> Optional[NotificationInDB]:
        """Fetch a notification by its ID"""
        return await self.notification_repository.get(notification_id)

    async def list_notifications(self, limit: int = 100, skip: int = 0) -> List[NotificationInDB]:
        """List all notifications"""
        return await self.notification_repository.list(limit=limit, skip=skip)

    async def list_notifications_by_user(
        self,
        user_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[NotificationInDB]:
        """Fetch all notifications for a user"""
        return await self.notification_repository.get_by_user_id(user_id, limit=limit, skip=skip)

    async def list_unread_notifications(
        self,
        user_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[NotificationInDB]:
        """Fetch all unread notifications for a user"""
        return await self.notification_repository.get_unread(user_id, limit=limit, skip=skip)

    async def mark_notification_as_read(self, notification_id: str) -> Optional[NotificationInDB]:
        """Mark a specific notification as read"""
        return await self.notification_repository.mark_as_read(notification_id)

    async def mark_all_notifications_as_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read"""
        return await self.notification_repository.mark_all_as_read(user_id)

    async def update_notification(
        self,
        notification_id: str,
        schema: NotificationUpdateSchema,
    ) -> Optional[NotificationInDB]:
        """Update an existing notification record"""
        update = NotificationUpdate(**schema.model_dump(exclude_unset=True))
        return await self.notification_repository.update(notification_id, update)

    async def delete_notification(self, notification_id: str) -> bool:
        """Permanently delete a notification record"""
        return await self.notification_repository.delete(notification_id)

    def to_response(self, notification: NotificationInDB) -> NotificationResponse:
        """Convert internal model to API response"""
        return _notification_to_response(notification)
