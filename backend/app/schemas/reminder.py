"""
Nura - Patient Reminder Schemas
Pydantic v2 schemas for reminder API requests and responses
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.reminder import (
    ReminderType,
    ReminderStatus,
    ReminderSourceType,
)


class ReminderCreateSchema(BaseModel):
    """Request schema for creating a new reminder"""
    patient_id: str = Field(..., description="Reference to the patient user ID")
    reminder_type: ReminderType = Field(..., description="Type of reminder")
    title: str = Field(..., min_length=1, max_length=200, description="Title of the reminder")
    description: Optional[str] = Field(None, max_length=2000, description="Optional description of the reminder")
    scheduled_time: str = Field(..., description="Scheduled time/date (HH:MM or ISO datetime string)")
    recurrence: Optional[str] = Field(None, max_length=100, description="Recurrence rule (e.g. daily, weekly, none)")
    status: ReminderStatus = Field(default=ReminderStatus.ACTIVE, description="Status of the reminder")
    source_type: ReminderSourceType = Field(default=ReminderSourceType.MANUAL, description="Source type")
    source_id: Optional[str] = Field(None, description="Optional reference to the source entity ID")


class ReminderUpdateSchema(BaseModel):
    """Request schema for updating an existing reminder"""
    patient_id: Optional[str] = None
    reminder_type: Optional[ReminderType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    scheduled_time: Optional[str] = None
    recurrence: Optional[str] = Field(None, max_length=100)
    status: Optional[ReminderStatus] = None
    source_type: Optional[ReminderSourceType] = None
    source_id: Optional[str] = None


class ReminderResponse(BaseModel):
    """Response schema for a patient reminder"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Reminder ID")
    patient_id: str = Field(..., description="Patient user ID")
    reminder_type: ReminderType = Field(..., description="Type of reminder")
    title: str = Field(..., description="Title of the reminder")
    description: Optional[str] = Field(None, description="Description of the reminder")
    scheduled_time: str = Field(..., description="Scheduled time/date")
    recurrence: Optional[str] = Field(None, description="Recurrence rule")
    status: ReminderStatus = Field(..., description="Status of the reminder")
    source_type: ReminderSourceType = Field(..., description="Source type")
    source_id: Optional[str] = Field(None, description="Source entity ID")
    created_at: datetime = Field(..., description="Reminder creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
