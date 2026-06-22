"""
Nura - Doctor Schemas
Pydantic v2 schemas for doctor API requests and responses
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.doctor import (
    DoctorProfileStatus,
    DocumentType,
    DocumentVerificationStatus,
    DayOfWeek,
)


# ---------------------------------------------------------------------------
# Doctor Profile Schemas
# ---------------------------------------------------------------------------

class DoctorProfileCreateSchema(BaseModel):
    """Request schema for creating a new doctor profile"""
    specialization: str = Field(..., min_length=1, max_length=200, description="Medical specialization")
    qualifications: List[str] = Field(default_factory=list, description="Qualifications list")
    experience_years: int = Field(..., ge=0, le=80, description="Years of experience")
    consultation_fee: float = Field(..., ge=0, description="Consultation fee in INR")
    bio: Optional[str] = Field(None, max_length=2000, description="Doctor biography")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    hospital: Optional[str] = Field(None, max_length=300, description="Hospital or clinic affiliation")
    license_number: Optional[str] = Field(None, max_length=100, description="Medical license number")
    education: Optional[str] = Field(None, max_length=500, description="Education details")


class DoctorProfileUpdateSchema(BaseModel):
    """Request schema for updating an existing doctor profile"""
    specialization: Optional[str] = Field(None, min_length=1, max_length=200)
    qualifications: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=80)
    consultation_fee: Optional[float] = Field(None, ge=0)
    bio: Optional[str] = Field(None, max_length=2000)
    languages: Optional[List[str]] = None
    hospital: Optional[str] = Field(None, max_length=300)
    license_number: Optional[str] = Field(None, max_length=100)
    education: Optional[str] = Field(None, max_length=500)


class DoctorProfileResponse(BaseModel):
    """Response schema for a doctor profile"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Doctor profile ID")
    user_id: str = Field(..., description="Associated user ID")
    specialization: str = Field(..., description="Medical specialization")
    qualifications: List[str] = Field(..., description="Qualifications list")
    experience_years: int = Field(..., description="Years of experience")
    consultation_fee: float = Field(..., description="Consultation fee in INR")
    bio: Optional[str] = Field(None, description="Doctor biography")
    languages: List[str] = Field(..., description="Languages spoken")
    hospital: Optional[str] = Field(None, description="Hospital or clinic affiliation")
    license_number: Optional[str] = Field(None, description="Medical license number")
    education: Optional[str] = Field(None, description="Education details")
    profile_status: DoctorProfileStatus = Field(..., description="Verification status")
    average_rating: float = Field(..., description="Average rating (0-5)")
    total_reviews: int = Field(..., description="Total reviews count")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Doctor Document Schemas
# ---------------------------------------------------------------------------

class DoctorDocumentCreateSchema(BaseModel):
    """Request schema for uploading a new verification document"""
    document_type: DocumentType = Field(..., description="Type of the document")
    document_url: str = Field(..., description="Publicly accessible URL of the document")


class DoctorDocumentUpdateSchema(BaseModel):
    """Request schema for updating a verification document"""
    document_type: Optional[DocumentType] = None
    document_url: Optional[str] = None
    verification_status: Optional[DocumentVerificationStatus] = None


class DoctorDocumentResponse(BaseModel):
    """Response schema for a doctor document"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Document ID")
    doctor_id: str = Field(..., description="Associated doctor profile ID")
    document_type: DocumentType = Field(..., description="Type of the document")
    document_url: str = Field(..., description="Document URL")
    verification_status: DocumentVerificationStatus = Field(..., description="Verification status")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    verified_by: Optional[str] = Field(None, description="Admin user ID who verified")


# ---------------------------------------------------------------------------
# Doctor Availability Schemas
# ---------------------------------------------------------------------------

class DoctorAvailabilityCreateSchema(BaseModel):
    """Request schema for creating a new availability slot"""
    day_of_week: DayOfWeek = Field(..., description="Day of the week")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Start time (HH:MM)")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="End time (HH:MM)")
    slot_duration: int = Field(default=30, ge=5, le=240, description="Slot duration in minutes")
    active: bool = Field(default=True, description="Whether availability is active")


class DoctorAvailabilityUpdateSchema(BaseModel):
    """Request schema for updating an existing availability slot"""
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    slot_duration: Optional[int] = Field(None, ge=5, le=240)
    active: Optional[bool] = None


class DoctorAvailabilityResponse(BaseModel):
    """Response schema for a doctor availability slot"""
    id: str = Field(..., description="Availability record ID")
    doctor_id: str = Field(..., description="Associated doctor profile ID")
    day_of_week: DayOfWeek = Field(..., description="Day of the week")
    start_time: str = Field(..., description="Start time (HH:MM)")
    end_time: str = Field(..., description="End time (HH:MM)")
    slot_duration: int = Field(..., description="Slot duration in minutes")
    active: bool = Field(..., description="Whether availability is active")


# ---------------------------------------------------------------------------
# Doctor Application Schemas
# ---------------------------------------------------------------------------

class DoctorApplicationRequest(BaseModel):
    """Request schema for submitting a doctor application"""
    specialization: str = Field(..., min_length=1, max_length=200, description="Medical specialization")
    experience_years: int = Field(..., ge=0, le=80, description="Years of medical experience")
    consultation_fee: float = Field(..., ge=0, description="Consultation fee in INR")
    bio: Optional[str] = Field(None, max_length=2000, description="Doctor biography/description")
    education: str = Field(..., min_length=1, max_length=500, description="Education details")
    languages: List[str] = Field(..., description="Languages spoken")
    hospital: Optional[str] = Field(None, max_length=300, description="Hospital or clinic affiliation")
    license_number: Optional[str] = Field(None, max_length=100, description="Medical license number")

    # Document metadata
    degree_certificate_url: str = Field(..., description="URL of the degree certificate document")
    medical_license_url: str = Field(..., description="URL of the medical license document")
    identity_proof_url: str = Field(..., description="URL of the identity proof document")


class DoctorApplicationUpdateSchema(BaseModel):
    """Request schema for updating a pending doctor application"""
    specialization: Optional[str] = Field(None, min_length=1, max_length=200)
    experience_years: Optional[int] = Field(None, ge=0, le=80)
    consultation_fee: Optional[float] = Field(None, ge=0)
    bio: Optional[str] = Field(None, max_length=2000)
    education: Optional[str] = Field(None, max_length=500)
    languages: Optional[List[str]] = None
    hospital: Optional[str] = Field(None, max_length=300)
    license_number: Optional[str] = Field(None, max_length=100)

    # Document metadata (all optional)
    degree_certificate_url: Optional[str] = None
    medical_license_url: Optional[str] = None
    identity_proof_url: Optional[str] = None


class DoctorApplicationResponse(BaseModel):
    """Response schema for retrieving doctor application status and details"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    application_status: str = Field(..., description="Overall application status (e.g. 'Pending Review')")
    profile_status: DoctorProfileStatus = Field(..., description="Status of the profile")
    profile: DoctorProfileResponse = Field(..., description="Detailed profile data")
    documents: List[DoctorDocumentResponse] = Field(..., description="List of verification documents")
