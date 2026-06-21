"""
Nura - Appointment, Consultation, and Prescription Schemas
Pydantic v2 schemas for appointment, consultation, and prescription API requests and responses
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.appointment import AppointmentStatus, PaymentStatus


# ---------------------------------------------------------------------------
# Appointment Schemas
# ---------------------------------------------------------------------------

class AppointmentCreateSchema(BaseModel):
    """Request schema for creating a new appointment"""
    doctor_id: str = Field(..., description="Reference to the doctor profile ID")
    slot_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date of the slot (YYYY-MM-DD)")
    slot_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Time of the slot (HH:MM)")
    duration_minutes: int = Field(default=30, ge=5, le=240, description="Duration in minutes")
    consultation_fee: float = Field(..., ge=0, description="Consultation fee in INR")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional patient notes")


class AppointmentUpdateSchema(BaseModel):
    """Request schema for updating an existing appointment"""
    doctor_id: Optional[str] = None
    slot_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    slot_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    duration_minutes: Optional[int] = Field(None, ge=5, le=240)
    consultation_fee: Optional[float] = Field(None, ge=0)
    status: Optional[AppointmentStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)


class AppointmentResponse(BaseModel):
    """Response schema for an appointment"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Appointment ID")
    patient_id: str = Field(..., description="Patient user ID")
    doctor_id: str = Field(..., description="Doctor profile ID")
    slot_date: str = Field(..., description="Date of the slot (YYYY-MM-DD)")
    slot_time: str = Field(..., description="Time of the slot (HH:MM)")
    duration_minutes: int = Field(..., description="Duration in minutes")
    consultation_fee: float = Field(..., description="Consultation fee in INR")
    status: AppointmentStatus = Field(..., description="Appointment status")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    notes: Optional[str] = Field(None, description="Optional patient notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Consultation Schemas
# ---------------------------------------------------------------------------

class ConsultationCreateSchema(BaseModel):
    """Request schema for creating a new consultation"""
    appointment_id: str = Field(..., description="Reference to the appointment ID")
    patient_id: str = Field(..., description="Reference to the patient user ID")
    doctor_id: str = Field(..., description="Reference to the doctor profile ID")
    consultation_notes: str = Field(..., min_length=1, max_length=5000, description="Notes written by the doctor")
    diagnosis: str = Field(..., min_length=1, max_length=2000, description="Diagnosis details")
    recommendations: str = Field(..., min_length=1, max_length=3000, description="Treatment and other recommendations")
    follow_up_required: bool = Field(default=False, description="Whether a follow-up is required")
    follow_up_date: Optional[datetime] = Field(None, description="Optional follow-up date")


class ConsultationUpdateSchema(BaseModel):
    """Request schema for updating an existing consultation"""
    consultation_notes: Optional[str] = Field(None, max_length=5000)
    diagnosis: Optional[str] = Field(None, max_length=2000)
    recommendations: Optional[str] = Field(None, max_length=3000)
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None


class ConsultationResponse(BaseModel):
    """Response schema for a consultation"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Consultation ID")
    appointment_id: str = Field(..., description="Appointment ID")
    patient_id: str = Field(..., description="Patient user ID")
    doctor_id: str = Field(..., description="Doctor profile ID")
    consultation_notes: str = Field(..., description="Notes written by the doctor")
    diagnosis: str = Field(..., description="Diagnosis details")
    recommendations: str = Field(..., description="Treatment and other recommendations")
    follow_up_required: bool = Field(..., description="Whether a follow-up is required")
    follow_up_date: Optional[datetime] = Field(None, description="Optional follow-up date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Prescription Schemas
# ---------------------------------------------------------------------------

class MedicationSchema(BaseModel):
    """Medication details representation in schemas"""
    drug_name: str = Field(..., min_length=1, max_length=200, description="Name of the drug")
    dosage: str = Field(..., min_length=1, max_length=100, description="Dosage (e.g. 500mg)")
    frequency: str = Field(..., min_length=1, max_length=100, description="Frequency (e.g. once daily)")
    duration: str = Field(..., min_length=1, max_length=100, description="Duration (e.g. 5 days)")


class PrescriptionCreateSchema(BaseModel):
    """Request schema for creating a new prescription"""
    consultation_id: str = Field(..., description="Reference to the consultation ID")
    patient_id: str = Field(..., description="Reference to the patient user ID")
    doctor_id: str = Field(..., description="Reference to the doctor profile ID")
    medications: List[MedicationSchema] = Field(..., min_items=1, description="List of prescribed medications")
    dosage_instructions: Optional[str] = Field(None, max_length=2000, description="Additional dosage instructions")
    notes: Optional[str] = Field(None, max_length=2000, description="General notes about the prescription")


class PrescriptionUpdateSchema(BaseModel):
    """Request schema for updating an existing prescription"""
    medications: Optional[List[MedicationSchema]] = Field(None, min_items=1)
    dosage_instructions: Optional[str] = Field(None, max_length=2000)
    notes: Optional[str] = Field(None, max_length=2000)


class PrescriptionResponse(BaseModel):
    """Response schema for a prescription"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Prescription ID")
    consultation_id: str = Field(..., description="Consultation ID")
    patient_id: str = Field(..., description="Patient user ID")
    doctor_id: str = Field(..., description="Doctor profile ID")
    medications: List[MedicationSchema] = Field(..., description="List of prescribed medications")
    dosage_instructions: Optional[str] = Field(None, description="Additional dosage instructions")
    notes: Optional[str] = Field(None, description="General notes about the prescription")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
