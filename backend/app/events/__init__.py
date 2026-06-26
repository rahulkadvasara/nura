"""
Nura - Events Package
Exports event models, dispatcher, and async processor queue
"""

from app.events.base import (
    BaseEvent,
    ReportUploadedEvent,
    ConsultationCompletedEvent,
    PrescriptionCreatedEvent,
    PrescriptionUpdatedEvent,
    ReminderCreatedEvent,
    ReminderUpdatedEvent,
    PatientProfileUpdatedEvent,
    AppointmentCompletedEvent,
    DoctorNotesUpdatedEvent,
    MedicalHistoryUpdatedEvent,
)
from app.events.dispatcher import EventDispatcher
from app.events.queue import EventQueue

__all__ = [
    "BaseEvent",
    "ReportUploadedEvent",
    "ConsultationCompletedEvent",
    "PrescriptionCreatedEvent",
    "PrescriptionUpdatedEvent",
    "ReminderCreatedEvent",
    "ReminderUpdatedEvent",
    "PatientProfileUpdatedEvent",
    "AppointmentCompletedEvent",
    "DoctorNotesUpdatedEvent",
    "MedicalHistoryUpdatedEvent",
    "EventDispatcher",
    "EventQueue",
]
