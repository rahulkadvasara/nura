"""
Nura - Patient Reminder Models
MongoDB models for reminders collection
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

class ReminderType(str, Enum):
    """Supported types of patient reminders"""
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    HEALTH_CHECK = "health_check"
    CUSTOM = "custom"


class ReminderStatus(str, Enum):
    """Current status of a reminder"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReminderSourceType(str, Enum):
    """Source that triggered the reminder creation"""
    PRESCRIPTION = "prescription"
    APPOINTMENT = "appointment"
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------

class ReminderBase(BaseModel):
    """Base fields shared by patient reminder models"""
    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(..., description="Reference to the patient user ID")
    reminder_type: ReminderType = Field(..., description="Type of reminder")
    title: str = Field(..., min_length=1, max_length=200, description="Title of the reminder")
    description: Optional[str] = Field(None, max_length=2000, description="Optional description of the reminder")
    scheduled_time: str = Field(..., description="Scheduled time/date (HH:MM or datetime string)")
    recurrence: Optional[str] = Field(None, max_length=100, description="Recurrence rule (e.g. daily, weekly, none)")
    status: ReminderStatus = Field(default=ReminderStatus.ACTIVE, description="Status of the reminder")
    source_type: ReminderSourceType = Field(default=ReminderSourceType.MANUAL, description="Source type")
    source_id: Optional[str] = Field(None, description="Optional reference to the source entity ID")


class ReminderCreate(ReminderBase):
    """Model used to create a new reminder record"""
    pass


class ReminderUpdate(BaseModel):
    """Model used to update an existing reminder record"""
    patient_id: Optional[str] = None
    reminder_type: Optional[ReminderType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    scheduled_time: Optional[str] = None
    recurrence: Optional[str] = Field(None, max_length=100)
    status: Optional[ReminderStatus] = None
    source_type: Optional[ReminderSourceType] = None
    source_id: Optional[str] = None


class ReminderInDB(ReminderBase):
    """Reminder as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "ReminderInDB":
        """Create ReminderInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("patient_id", "source_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)
