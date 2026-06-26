"""
Nura - Event Base Models
Pydantic event model definitions for event-driven memory synchronization
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class BaseEvent(BaseModel):
    """Base fields shared by all application events"""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the event instance")
    event_type: str = Field(..., description="The name/type of the event topic")
    timestamp: datetime = Field(default_factory=utc_now, description="Event generation timestamp")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event key-value payload parameters")


# Specific Event Subclasses
class ReportUploadedEvent(BaseEvent):
    """Event triggered when a new medical report is uploaded or processed"""
    def __init__(self, patient_id: str, report_id: str, uploaded_by: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            "report_id": report_id,
            "uploaded_by": uploaded_by,
            **kwargs
        }
        super().__init__(event_type="ReportUploaded", payload=payload)


class ConsultationCompletedEvent(BaseEvent):
    """Event triggered when a doctor consultation is successfully completed"""
    def __init__(self, patient_id: str, consultation_id: str, doctor_id: str, appointment_id: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            "consultation_id": consultation_id,
            "doctor_id": doctor_id,
            "appointment_id": appointment_id,
            **kwargs
        }
        super().__init__(event_type="ConsultationCompleted", payload=payload)


class PrescriptionCreatedEvent(BaseEvent):
    """Event triggered when a new prescription is issued for a consultation"""
    def __init__(self, patient_id: str, prescription_id: str, doctor_id: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            "prescription_id": prescription_id,
            "doctor_id": doctor_id,
            **kwargs
        }
        super().__init__(event_type="PrescriptionCreated", payload=payload)


class PrescriptionUpdatedEvent(BaseEvent):
    """Event triggered when an existing prescription is modified"""
    def __init__(self, patient_id: str, prescription_id: str, doctor_id: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            "prescription_id": prescription_id,
            "doctor_id": doctor_id,
            **kwargs
        }
        super().__init__(event_type="PrescriptionUpdated", payload=payload)


class ReminderCreatedEvent(BaseEvent):
    """Event triggered when a medication/consultation reminder is created"""
    def __init__(self, patient_id: str, reminder_id: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            "reminder_id": reminder_id,
            **kwargs
        }
        super().__init__(event_type="ReminderCreated", payload=payload)


class ReminderUpdatedEvent(BaseEvent):
    """Event triggered when an existing reminder is modified"""
    def __init__(self, patient_id: str, reminder_id: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            "reminder_id": reminder_id,
            **kwargs
        }
        super().__init__(event_type="ReminderUpdated", payload=payload)


class PatientProfileUpdatedEvent(BaseEvent):
    """Event triggered when patient profile demographics or settings change"""
    def __init__(self, patient_id: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            **kwargs
        }
        super().__init__(event_type="PatientProfileUpdated", payload=payload)


class AppointmentCompletedEvent(BaseEvent):
    """Event triggered when an appointment status transitions to completed"""
    def __init__(self, patient_id: str, appointment_id: str, doctor_id: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "doctor_id": doctor_id,
            **kwargs
        }
        super().__init__(event_type="AppointmentCompleted", payload=payload)


class DoctorNotesUpdatedEvent(BaseEvent):
    """Event triggered when a doctor modifies clinical consultation notes"""
    def __init__(self, patient_id: str, consultation_id: str, doctor_id: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            "consultation_id": consultation_id,
            "doctor_id": doctor_id,
            **kwargs
        }
        super().__init__(event_type="DoctorNotesUpdated", payload=payload)


class MedicalHistoryUpdatedEvent(BaseEvent):
    """Event triggered when a patient's historical medical records or chronic profile is updated"""
    def __init__(self, patient_id: str, **kwargs):
        payload = {
            "patient_id": patient_id,
            **kwargs
        }
        super().__init__(event_type="MedicalHistoryUpdated", payload=payload)
