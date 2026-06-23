"""
Nura - Appointment, Consultation, and Prescription Models
MongoDB models for appointments, consultations, and prescriptions collections
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class AppointmentStatus(str, Enum):
    """Status of an appointment"""
    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentStatus(str, Enum):
    """Payment status for an appointment"""
    PENDING = "pending"
    HELD = "held"
    APPROVED = "approved"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

class AppointmentBase(BaseModel):
    """Base fields shared by appointment models"""
    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(..., description="Reference to the patient user ID")
    doctor_id: str = Field(..., description="Reference to the doctor profile ID")
    availability_id: Optional[str] = Field(None, description="Reference to the doctor availability slot ID")
    slot_date: str = Field(..., description="Date of the slot (YYYY-MM-DD)")
    slot_time: str = Field(..., description="Time of the slot (HH:MM)")
    duration_minutes: int = Field(default=30, ge=5, le=240, description="Duration in minutes")
    consultation_fee: float = Field(..., ge=0, description="Consultation fee in INR")
    status: AppointmentStatus = Field(default=AppointmentStatus.PENDING, description="Appointment status")
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Payment status")
    reason: Optional[str] = Field(None, description="Reason for visit")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional patient notes")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejecting the appointment")
    consultation_started_at: Optional[datetime] = Field(None, description="Timestamp of when the consultation started")
    consultation_completed_at: Optional[datetime] = Field(None, description="Timestamp of when the consultation completed")


class AppointmentCreate(AppointmentBase):
    """Model used to create a new appointment"""
    pass


class AppointmentUpdate(BaseModel):
    """Model used to update an existing appointment"""
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    availability_id: Optional[str] = None
    slot_date: Optional[str] = None
    slot_time: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=240)
    consultation_fee: Optional[float] = Field(None, ge=0)
    status: Optional[AppointmentStatus] = None
    payment_status: Optional[PaymentStatus] = None
    reason: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    rejection_reason: Optional[str] = None
    consultation_started_at: Optional[datetime] = None
    consultation_completed_at: Optional[datetime] = None


class AppointmentInDB(AppointmentBase):
    """Appointment as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "AppointmentInDB":
        """Create AppointmentInDB from raw MongoDB document converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("patient_id", "doctor_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)


# ---------------------------------------------------------------------------
# Consultations
# ---------------------------------------------------------------------------

class ConsultationBase(BaseModel):
    """Base fields shared by consultation models"""
    model_config = ConfigDict(populate_by_name=True)

    appointment_id: str = Field(..., description="Reference to the appointment ID")
    patient_id: str = Field(..., description="Reference to the patient user ID")
    doctor_id: str = Field(..., description="Reference to the doctor profile ID")
    consultation_notes: str = Field(..., max_length=5000, description="Notes written by the doctor")
    diagnosis: str = Field(..., max_length=2000, description="Diagnosis details")
    recommendations: Optional[str] = Field(default=None, max_length=3000, description="Treatment and other recommendations")
    follow_up_required: bool = Field(default=False, description="Whether a follow-up is required")
    follow_up_date: Optional[datetime] = Field(None, description="Optional follow-up date")


class ConsultationCreate(ConsultationBase):
    """Model used to create a new consultation"""
    pass


class ConsultationUpdate(BaseModel):
    """Model used to update an existing consultation"""
    appointment_id: Optional[str] = None
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    consultation_notes: Optional[str] = Field(None, max_length=5000)
    diagnosis: Optional[str] = Field(None, max_length=2000)
    recommendations: Optional[str] = Field(None, max_length=3000)
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None


class ConsultationInDB(ConsultationBase):
    """Consultation as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "ConsultationInDB":
        """Create ConsultationInDB from raw MongoDB document converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("appointment_id", "patient_id", "doctor_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)


# ---------------------------------------------------------------------------
# Prescriptions
# ---------------------------------------------------------------------------

class Medication(BaseModel):
    """Representation of a single prescribed medication"""
    drug_name: str = Field(..., min_length=1, max_length=200, description="Name of the drug")
    dosage: str = Field(..., min_length=1, max_length=100, description="Dosage (e.g. 500mg, 1 tablet)")
    frequency: str = Field(..., min_length=1, max_length=100, description="Frequency (e.g. once daily, twice daily)")
    duration: str = Field(..., min_length=1, max_length=100, description="Duration (e.g. 5 days, 1 month)")


class PrescriptionBase(BaseModel):
    """Base fields shared by prescription models"""
    model_config = ConfigDict(populate_by_name=True)

    consultation_id: str = Field(..., description="Reference to the consultation ID")
    patient_id: str = Field(..., description="Reference to the patient user ID")
    doctor_id: str = Field(..., description="Reference to the doctor profile ID")
    medications: List[Medication] = Field(default_factory=list, description="List of prescribed medications")
    dosage_instructions: Optional[str] = Field(None, max_length=2000, description="Additional dosage instructions")
    notes: Optional[str] = Field(None, max_length=2000, description="General notes about the prescription")


class PrescriptionCreate(PrescriptionBase):
    """Model used to create a new prescription"""
    pass


class PrescriptionUpdate(BaseModel):
    """Model used to update an existing prescription"""
    consultation_id: Optional[str] = None
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    medications: Optional[List[Medication]] = None
    dosage_instructions: Optional[str] = Field(None, max_length=2000)
    notes: Optional[str] = Field(None, max_length=2000)


class PrescriptionInDB(PrescriptionBase):
    """Prescription as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "PrescriptionInDB":
        """Create PrescriptionInDB from raw MongoDB document converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("consultation_id", "patient_id", "doctor_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)
