"""
Nura - Dashboard Response Schemas
Read-only Pydantic v2 schemas for Patient, Doctor, and Admin dashboard API responses
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Shared sub-schemas
# ---------------------------------------------------------------------------

class RecentHealthInsight(BaseModel):
    """Compact health insight summary for dashboard display"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Health insight ID")
    title: str = Field(..., description="Short insight title")
    severity: Optional[str] = Field(None, description="Severity level (low/medium/high)")
    created_at: datetime = Field(..., description="When the insight was generated")


class PatientDashboardConsultation(BaseModel):
    """Compact consultation summary for dashboard display"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Consultation ID")
    doctor_name: str = Field(..., description="Doctor's full name")
    specialization: str = Field(..., description="Doctor's specialization")
    date: datetime = Field(..., description="Consultation/appointment date")
    diagnosis: str = Field(..., description="Diagnosis details")


class PatientDashboardPrescription(BaseModel):
    """Compact prescription summary for dashboard display"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Prescription ID")
    doctor_name: str = Field(..., description="Doctor's full name")
    date: datetime = Field(..., description="Prescription date")
    medications_count: int = Field(..., description="Number of medications in this prescription")


# ---------------------------------------------------------------------------
# Patient Dashboard
# ---------------------------------------------------------------------------

class PatientDashboardResponse(BaseModel):
    """Read-only aggregated data for the patient dashboard"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    upcoming_appointments_count: int = Field(
        default=0,
        description="Number of upcoming appointments (pending or approved, future dates)",
    )
    active_reminders_count: int = Field(
        default=0,
        description="Number of currently active reminders",
    )
    reports_count: int = Field(
        default=0,
        description="Total number of uploaded reports",
    )
    unread_notifications_count: int = Field(
        default=0,
        description="Number of unread notifications",
    )
    recent_health_insights: List[RecentHealthInsight] = Field(
        default_factory=list,
        description="Most recent health insights (up to 5)",
    )
    recent_consultation: Optional[PatientDashboardConsultation] = Field(
        default=None,
        description="Most recent completed consultation details"
    )
    recent_prescription: Optional[PatientDashboardPrescription] = Field(
        default=None,
        description="Most recent prescription details"
    )


# ---------------------------------------------------------------------------
# Doctor Dashboard
# ---------------------------------------------------------------------------

class DoctorDashboardResponse(BaseModel):
    """Read-only aggregated data for the doctor dashboard"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    todays_appointments_count: int = Field(
        default=0,
        description="Number of appointments scheduled for today",
    )
    upcoming_appointments_count: int = Field(
        default=0,
        description="Number of upcoming appointments (future dates, pending/approved)",
    )
    total_patients_count: int = Field(
        default=0,
        description="Total number of unique patients this doctor has appointments with",
    )
    pending_approvals_count: int = Field(
        default=0,
        description="Number of appointments awaiting the doctor's approval",
    )
    wallet_balance: float = Field(
        default=0.0,
        description="Current available wallet balance (INR)",
    )
    total_earnings: float = Field(
        default=0.0,
        description="Total lifetime earnings (INR)",
    )
    pending_balance: float = Field(
        default=0.0,
        description="Earnings currently held in escrow/pending (INR)",
    )
    profile_status: str = Field(
        default="pending",
        description="Verification status of the doctor profile (pending/verified/rejected)",
    )
    document_status: str = Field(
        default="pending",
        description="Verification status of the doctor documents (pending/approved/rejected)",
    )
    prescriptions_written_count: int = Field(
        default=0,
        description="Total number of prescriptions written by this doctor"
    )




# ---------------------------------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------------------------------

class AdminDashboardResponse(BaseModel):
    """Read-only aggregated data for the admin dashboard"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    total_users_count: int = Field(
        default=0,
        description="Total number of registered users on the platform",
    )
    total_patients_count: int = Field(
        default=0,
        description="Total number of patient-role users",
    )
    total_doctors_count: int = Field(
        default=0,
        description="Total number of doctor-role users",
    )
    pending_doctor_verifications_count: int = Field(
        default=0,
        description="Number of doctor profiles pending admin verification",
    )
    total_appointments_count: int = Field(
        default=0,
        description="Total appointments across the platform",
    )
    total_revenue: float = Field(
        default=0.0,
        description="Total revenue collected (sum of all payment amounts, INR)",
    )
    platform_earnings: float = Field(
        default=0.0,
        description="Total platform earnings from fee splits, INR",
    )
    active_consultations_count: int = Field(
        default=0,
        description="Total number of consultation records on the platform",
    )
    reports_count: int = Field(
        default=0,
        description="Total number of uploaded reports across the platform",
    )
    reminders_count: int = Field(
        default=0,
        description="Total number of active reminders across the platform",
    )
    active_chats_count: int = Field(
        default=0,
        description="Total number of active chat sessions on the platform",
    )
    verified_doctors_count: int = Field(
        default=0,
        description="Total number of verified doctor profiles",
    )

