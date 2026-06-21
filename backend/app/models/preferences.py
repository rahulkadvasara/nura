"""
Nura - Notification Preferences Model
"""

from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class NotificationPreferencesBase(BaseModel):
    """Base model for notification preferences"""
    email_enabled: bool = Field(default=True, description="Enable email notifications")
    appointment_enabled: bool = Field(default=True, description="Enable appointment updates")
    reminder_enabled: bool = Field(default=True, description="Enable medication/health reminders")
    report_enabled: bool = Field(default=True, description="Enable report analysis updates")
    marketing_enabled: bool = Field(default=False, description="Enable marketing emails")


class NotificationPreferencesUpdate(BaseModel):
    """Update model for notification preferences"""
    email_enabled: Optional[bool] = None
    appointment_enabled: Optional[bool] = None
    reminder_enabled: Optional[bool] = None
    report_enabled: Optional[bool] = None
    marketing_enabled: Optional[bool] = None


class NotificationPreferencesInDB(NotificationPreferencesBase):
    """Database model for notification preferences"""
    id: str = Field(..., description="Preference Document ID")
    user_id: str = Field(..., description="User ID associated with preferences")

    @classmethod
    def from_mongo(cls, data: dict) -> "NotificationPreferencesInDB":
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        if "user_id" in doc and isinstance(doc["user_id"], ObjectId):
            doc["user_id"] = str(doc["user_id"])
        return cls(**doc)


class NotificationPreferencesResponse(NotificationPreferencesBase):
    """Response model for notification preferences"""
    id: str = Field(..., description="Preference Document ID")
    user_id: str = Field(..., description="User ID associated with preferences")
