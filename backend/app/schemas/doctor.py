"""
Nura - Doctor Schemas
Pydantic v2 schemas for doctor API requests and responses
"""

from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.models.storage import FileMetadata

from app.models.doctor import (
    DoctorProfileStatus,
    DocumentType,
    DocumentVerificationStatus,
    DayOfWeek,
)
from app.schemas.auth import TokenUser


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
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if applicable")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Doctor Document Schemas
# ---------------------------------------------------------------------------

class DoctorDocumentCreateSchema(BaseModel):
    """Request schema for uploading a new verification document"""
    document_type: DocumentType = Field(..., description="Type of the document")
    document_url: str = Field(..., description="Publicly accessible URL of the document")
    document_metadata: Optional[FileMetadata] = Field(None, description="Detailed file metadata")


class DoctorDocumentUpdateSchema(BaseModel):
    """Request schema for updating a verification document"""
    document_type: Optional[DocumentType] = None
    document_url: Optional[str] = None
    document_metadata: Optional[FileMetadata] = None
    verification_status: Optional[DocumentVerificationStatus] = None


class DoctorDocumentResponse(BaseModel):
    """Response schema for a doctor document"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Document ID")
    doctor_id: str = Field(..., description="Associated doctor profile ID")
    document_type: DocumentType = Field(..., description="Type of the document")
    document_url: str = Field(..., description="Document URL")
    document_metadata: Optional[FileMetadata] = Field(None, description="Detailed file metadata")
    verification_status: DocumentVerificationStatus = Field(..., description="Verification status")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    verified_by: Optional[str] = Field(None, description="Admin user ID who verified")


# ---------------------------------------------------------------------------
# Doctor Availability Schemas
# ---------------------------------------------------------------------------

class DoctorAvailabilityCreateSchema(BaseModel):
    """Request schema for creating a new availability slot"""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Slot date (YYYY-MM-DD)")
    day_of_week: Optional[DayOfWeek] = Field(None, description="Day of the week")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Start time (HH:MM)")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="End time (HH:MM)")
    slot_duration: int = Field(default=30, ge=5, le=240, description="Slot duration in minutes")
    is_available: bool = Field(default=True, description="Whether slot is available")
    active: bool = Field(default=True, description="Whether availability is active")

    @model_validator(mode="before")
    @classmethod
    def set_day_of_week(cls, data: Any) -> Any:
        if isinstance(data, dict):
            date_val = data.get("date")
            if date_val and not data.get("day_of_week"):
                try:
                    dt = datetime.strptime(date_val, "%Y-%m-%d")
                    day_name = dt.strftime("%A").lower()
                    data["day_of_week"] = day_name
                except Exception:
                    pass
        return data


class DoctorAvailabilityUpdateSchema(BaseModel):
    """Request schema for updating an existing availability slot"""
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    slot_duration: Optional[int] = Field(None, ge=5, le=240)
    is_available: Optional[bool] = None
    active: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def set_day_of_week(cls, data: Any) -> Any:
        if isinstance(data, dict):
            date_val = data.get("date")
            if date_val and not data.get("day_of_week"):
                try:
                    dt = datetime.strptime(date_val, "%Y-%m-%d")
                    day_name = dt.strftime("%A").lower()
                    data["day_of_week"] = day_name
                except Exception:
                    pass
        return data


class DoctorAvailabilityResponse(BaseModel):
    """Response schema for a doctor availability slot"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Availability record ID")
    doctor_id: str = Field(..., description="Associated doctor profile ID")
    date: str = Field(..., description="Slot date (YYYY-MM-DD)")
    day_of_week: DayOfWeek = Field(..., description="Day of the week")
    start_time: str = Field(..., description="Start time (HH:MM)")
    end_time: str = Field(..., description="End time (HH:MM)")
    slot_duration: int = Field(..., description="Slot duration in minutes")
    is_available: bool = Field(..., description="Whether slot is available")
    active: bool = Field(..., description="Whether availability is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


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
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if applicable")


# ---------------------------------------------------------------------------
# Admin Verification Schemas
# ---------------------------------------------------------------------------

class AdminDoctorListResponse(BaseModel):
    """Response schema representing an item in the admin review queue"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Doctor profile ID")
    user_id: str = Field(..., description="Associated user ID")
    full_name: str = Field(..., description="Full name of applicant")
    email: str = Field(..., description="Email address of applicant")
    specialization: str = Field(..., description="Medical specialization")
    experience_years: int = Field(..., description="Years of experience")
    consultation_fee: float = Field(..., description="Consultation fee in INR")
    hospital: Optional[str] = Field(None, description="Hospital affiliation")
    license_number: Optional[str] = Field(None, description="Medical license number")
    education: Optional[str] = Field(None, description="Education details")
    profile_status: DoctorProfileStatus = Field(..., description="Verification status")
    created_at: datetime = Field(..., description="Submission date")
    is_active: Optional[bool] = Field(None, description="User account active status")



class DoctorVerificationResponse(BaseModel):
    """Full detail response of an applicant for admin review"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    profile: DoctorProfileResponse = Field(..., description="Detailed profile data")
    user: TokenUser = Field(..., description="Associated user data")
    documents: List[DoctorDocumentResponse] = Field(..., description="Submitted credentials and documents")


class DoctorApprovalRequest(BaseModel):
    """Request payload for doctor approval (currently empty)"""
    pass


class DoctorRejectionRequest(BaseModel):
    """Request payload for doctor rejection containing reason"""
    rejection_reason: str = Field(..., min_length=1, description="Reason for rejecting the credentials")


class DoctorProfileManagementUpdateSchema(BaseModel):
    """Request schema for doctor self-updating their professional profile"""
    bio: Optional[str] = Field(None, max_length=2000, description="Doctor biography")
    consultation_fee: Optional[float] = Field(None, ge=0, description="Consultation fee in INR")
    languages: Optional[List[str]] = Field(None, description="Languages spoken")
    education: Optional[str] = Field(None, max_length=500, description="Education details")
    experience_years: Optional[int] = Field(None, ge=0, le=80, description="Years of experience")


class DoctorProfileManagementResponse(BaseModel):
    """Response schema containing the profile details and uploaded document statuses"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    profile: DoctorProfileResponse = Field(..., description="Doctor profile data")
    documents: List[DoctorDocumentResponse] = Field(..., description="Uploaded verification documents metadata")


class DoctorDiscoveryResponse(BaseModel):
    """Response schema representing a verified doctor profile details for patient discovery"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Doctor profile ID")
    user_id: str = Field(..., description="Associated user ID")
    name: str = Field(..., description="Full name of the doctor")
    specialization: str = Field(..., description="Medical specialization")
    qualifications: List[str] = Field(default_factory=list, description="Qualifications list")
    experience_years: int = Field(..., description="Years of experience")
    consultation_fee: float = Field(..., description="Consultation fee in INR")
    bio: Optional[str] = Field(None, description="Doctor biography")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    hospital: Optional[str] = Field(None, description="Hospital or clinic affiliation")
    education: Optional[str] = Field(None, description="Education details")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    average_rating: float = Field(..., description="Average rating")
    total_reviews: int = Field(..., description="Total reviews count")
