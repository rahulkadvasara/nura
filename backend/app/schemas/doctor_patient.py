"""
Nura - Doctor Patient Management Schemas
Pydantic schemas for retrieving doctor-specific patient list and detail profiles.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.appointment import AppointmentResponse, ConsultationResponse, PrescriptionResponse
from app.schemas.report import ReportResponse, HealthInsightResponse
from app.schemas.reminder import ReminderResponse
from app.schemas.chat import ChatSessionResponse
from app.models.user import UserResponse


class DoctorPatientSummary(BaseModel):
    """Schema representing a single patient summary in the doctor's patient directory"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    patient_id: str = Field(..., description="Patient's User ID")
    name: str = Field(..., description="Patient's full name")
    age: Optional[int] = Field(None, description="Patient's age (if available)")
    gender: Optional[str] = Field(None, description="Patient's gender (if available)")
    profile_picture: Optional[str] = Field(None, description="Patient's profile picture URL")
    latest_appointment: Optional[AppointmentResponse] = Field(None, description="Patient's latest appointment metadata with this doctor")
    latest_consultation: Optional[ConsultationResponse] = Field(None, description="Patient's latest consultation details with this doctor")
    total_appointments: int = Field(default=0, description="Total number of appointments booked with this doctor")
    total_consultations: int = Field(default=0, description="Total number of consultations completed with this doctor")
    total_reports: int = Field(default=0, description="Total number of reports uploaded by the patient")
    health_risk_level: Optional[str] = Field(None, description="Current health risk classification from patient's latest report analysis")


class DoctorPatientListResponse(BaseModel):
    """Response schema holding patient directory summaries list and total counts"""
    patients: List[DoctorPatientSummary] = Field(..., description="List of doctor's patient summaries")
    total: int = Field(..., description="Total unique patients matching query")


class DoctorPatientDetailResponse(BaseModel):
    """Response schema containing the complete patient profile details aggregated for the doctor"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    profile: UserResponse = Field(..., description="Patient user profile basic information")
    appointment_history: List[AppointmentResponse] = Field(default_factory=list, description="List of all appointments patient had with this doctor")
    consultation_history: List[ConsultationResponse] = Field(default_factory=list, description="List of all consultations patient completed with this doctor")
    reports: List[ReportResponse] = Field(default_factory=list, description="Medical reports uploaded by this patient")
    prescriptions: List[PrescriptionResponse] = Field(default_factory=list, description="Prescriptions written by this doctor for this patient")
    health_insights: List[HealthInsightResponse] = Field(default_factory=list, description="Health insights generated for this patient")
    current_reminders: List[ReminderResponse] = Field(default_factory=list, description="Active reminders set for this patient")
    latest_chat_session: Optional[ChatSessionResponse] = Field(None, description="Latest doctor-patient chat session details if exists")
