"""
Nura - Notification Schemas
Pydantic v2 schemas for notification API requests and responses
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.notification import (
    NotificationType,
    NotificationPriority,
)


class NotificationCreateSchema(BaseModel):
    """Request schema for creating a new notification"""
    user_id: str = Field(..., description="Reference to the recipient user ID")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., min_length=1, max_length=200, description="Title of the notification")
    message: str = Field(..., min_length=1, max_length=2000, description="Content message of the notification")
    read: bool = Field(default=False, description="Whether the notification has been read")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM, description="Priority level")
    related_entity_type: Optional[str] = Field(None, max_length=100, description="Optional entity type reference")
    related_entity_id: Optional[str] = Field(None, description="Optional reference to related entity ID")


class NotificationUpdateSchema(BaseModel):
    """Request schema for updating an existing notification"""
    user_id: Optional[str] = None
    notification_type: Optional[NotificationType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1, max_length=2000)
    read: Optional[bool] = None
    priority: Optional[NotificationPriority] = None
    related_entity_type: Optional[str] = Field(None, max_length=100)
    related_entity_id: Optional[str] = None


class NotificationResponse(BaseModel):
    """Response schema for a user notification"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Notification ID")
    user_id: str = Field(..., description="Recipient user ID")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., description="Title of the notification")
    message: str = Field(..., description="Content message of the notification")
    read: bool = Field(..., description="Whether the notification has been read")
    priority: NotificationPriority = Field(..., description="Priority level")
    related_entity_type: Optional[str] = Field(None, description="Related entity type")
    related_entity_id: Optional[str] = Field(None, description="Related entity ID")
    created_at: datetime = Field(..., description="Notification creation timestamp")
