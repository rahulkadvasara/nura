"""
Nura - Notification Models
MongoDB models for notifications collection
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class NotificationType(str, Enum):
    """Types of notifications sent to users"""
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    REPORT = "report"
    SYSTEM = "system"
    AI_INSIGHT = "ai_insight"
    APPOINTMENT_APPROVED = "appointment_approved"
    APPOINTMENT_REJECTED = "appointment_rejected"


class NotificationPriority(str, Enum):
    """Priority levels for notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class NotificationBase(BaseModel):
    """Base fields shared by user notification models"""
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(..., description="Reference to the recipient user ID")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., min_length=1, max_length=200, description="Title of the notification")
    message: str = Field(..., min_length=1, max_length=2000, description="Content message of the notification")
    read: bool = Field(default=False, description="Whether the notification has been read")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM, description="Priority level")
    related_entity_type: Optional[str] = Field(None, max_length=100, description="Optional entity type reference")
    related_entity_id: Optional[str] = Field(None, description="Optional reference to related entity ID")


class NotificationCreate(NotificationBase):
    """Model used to create a new notification record"""
    pass


class NotificationUpdate(BaseModel):
    """Model used to update an existing notification record"""
    user_id: Optional[str] = None
    notification_type: Optional[NotificationType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1, max_length=2000)
    read: Optional[bool] = None
    priority: Optional[NotificationPriority] = None
    related_entity_type: Optional[str] = Field(None, max_length=100)
    related_entity_id: Optional[str] = None


class NotificationInDB(NotificationBase):
    """Notification as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "NotificationInDB":
        """Create NotificationInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("user_id", "related_entity_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)
