"""
Nura - Notification Preferences Model
"""

from typing import Any, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, model_validator


class NotificationPreferencesBase(BaseModel):
    """Base model for notification preferences"""
    email_enabled: bool = Field(default=True, description="Enable email notifications")
    appointment_enabled: bool = Field(default=True, description="Enable appointment updates")
    reminder_enabled: bool = Field(default=True, description="Enable medication/health reminders")
    report_enabled: bool = Field(default=True, description="Enable report analysis updates")
    marketing_enabled: bool = Field(default=False, description="Enable marketing emails")

    # New fields for Sprint 4
    email_notifications: bool = Field(default=True, description="Enable email notifications")
    appointment_reminders: bool = Field(default=True, description="Enable appointment reminders")
    medication_reminders: bool = Field(default=True, description="Enable medication reminders")
    report_updates: bool = Field(default=True, description="Enable report updates")
    marketing_notifications: bool = Field(default=False, description="Enable marketing notifications")

    @model_validator(mode="before")
    @classmethod
    def sync_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            sync_pairs = [
                ("email_notifications", "email_enabled"),
                ("appointment_reminders", "appointment_enabled"),
                ("medication_reminders", "reminder_enabled"),
                ("report_updates", "report_enabled"),
                ("marketing_notifications", "marketing_enabled"),
            ]
            for new_f, old_f in sync_pairs:
                if new_f in data and old_f not in data:
                    data[old_f] = data[new_f]
                elif old_f in data and new_f not in data:
                    data[new_f] = data[old_f]
        return data


class NotificationPreferencesUpdate(BaseModel):
    """Update model for notification preferences"""
    email_enabled: Optional[bool] = None
    appointment_enabled: Optional[bool] = None
    reminder_enabled: Optional[bool] = None
    report_enabled: Optional[bool] = None
    marketing_enabled: Optional[bool] = None

    # New fields for Sprint 4
    email_notifications: Optional[bool] = None
    appointment_reminders: Optional[bool] = None
    medication_reminders: Optional[bool] = None
    report_updates: Optional[bool] = None
    marketing_notifications: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def sync_legacy_fields_update(cls, data: Any) -> Any:
        if isinstance(data, dict):
            sync_pairs = [
                ("email_notifications", "email_enabled"),
                ("appointment_reminders", "appointment_enabled"),
                ("medication_reminders", "reminder_enabled"),
                ("report_updates", "report_enabled"),
                ("marketing_notifications", "marketing_enabled"),
            ]
            for new_f, old_f in sync_pairs:
                if new_f in data and old_f not in data:
                    data[old_f] = data[new_f]
                elif old_f in data and new_f not in data:
                    data[new_f] = data[old_f]
        return data


class NotificationPreferencesInDB(NotificationPreferencesBase):
    """Database model for notification preferences"""
    id: str = Field(..., description="Preference Document ID")
    user_id: str = Field(..., description="User ID associated with preferences")

    @classmethod
    def from_mongo(cls, data: dict) -> "NotificationPreferencesInDB":
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        if "user_id" in doc and not isinstance(doc["user_id"], str):
            doc["user_id"] = str(doc["user_id"])
        return cls(**doc)


class NotificationPreferencesResponse(NotificationPreferencesBase):
    """Response model for notification preferences"""
    id: str = Field(..., description="Preference Document ID")
    user_id: str = Field(..., description="User ID associated with preferences")
