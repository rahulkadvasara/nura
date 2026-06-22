"""
Nura - Doctor Models
MongoDB models for doctor_profiles, doctor_documents, and doctor_availability collections
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

class DoctorProfileStatus(str, Enum):
    """Verification status for a doctor profile"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class DocumentType(str, Enum):
    """Supported document types for verification"""
    LICENSE = "license"
    DEGREE = "degree"
    CERTIFICATE = "certificate"
    ID_PROOF = "id_proof"
    OTHER = "other"


class DocumentVerificationStatus(str, Enum):
    """Verification status for uploaded documents"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DayOfWeek(str, Enum):
    """ISO day-of-week values"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# ---------------------------------------------------------------------------
# doctor_profiles
# ---------------------------------------------------------------------------

class DoctorProfileBase(BaseModel):
    """Base fields shared by create / update / in-DB doctor profile models"""
    model_config = ConfigDict(populate_by_name=True)

    specialization: str = Field(..., min_length=1, max_length=200, description="Doctor specialization")
    qualifications: List[str] = Field(default_factory=list, description="Academic and professional qualifications")
    experience_years: int = Field(..., ge=0, le=80, description="Years of medical experience")
    consultation_fee: float = Field(..., ge=0, description="Consultation fee in INR")
    bio: Optional[str] = Field(None, max_length=2000, description="Doctor bio")
    languages: List[str] = Field(default_factory=list, description="Languages the doctor speaks")
    hospital: Optional[str] = Field(None, max_length=300, description="Hospital or clinic affiliation")
    license_number: Optional[str] = Field(None, max_length=100, description="Medical license number")
    education: Optional[str] = Field(None, max_length=500, description="Doctor education/degrees")
    rejection_reason: Optional[str] = Field(None, max_length=1000, description="Reason for application rejection")


class DoctorProfileCreate(DoctorProfileBase):
    """Schema used to create a new doctor profile"""
    user_id: str = Field(..., description="Reference to the user who owns this profile")
    profile_status: DoctorProfileStatus = Field(
        default=DoctorProfileStatus.PENDING,
        description="Verification status of the profile",
    )
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Average rating from reviews")
    total_reviews: int = Field(default=0, ge=0, description="Total number of reviews")


class DoctorProfileUpdate(BaseModel):
    """Schema used to update an existing doctor profile (all fields optional)"""
    specialization: Optional[str] = Field(None, min_length=1, max_length=200)
    qualifications: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=80)
    consultation_fee: Optional[float] = Field(None, ge=0)
    bio: Optional[str] = Field(None, max_length=2000)
    languages: Optional[List[str]] = None
    hospital: Optional[str] = Field(None, max_length=300)
    license_number: Optional[str] = Field(None, max_length=100)
    education: Optional[str] = Field(None, max_length=500)
    rejection_reason: Optional[str] = Field(None, max_length=1000)
    profile_status: Optional[DoctorProfileStatus] = None
    average_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    total_reviews: Optional[int] = Field(None, ge=0)


class DoctorProfileInDB(DoctorProfileBase):
    """Doctor profile as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    user_id: str = Field(..., description="Reference to the owning user")
    profile_status: DoctorProfileStatus = Field(
        default=DoctorProfileStatus.PENDING,
        description="Verification status of the profile",
    )
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Average rating from reviews")
    total_reviews: int = Field(default=0, ge=0, description="Total number of reviews")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "DoctorProfileInDB":
        """Create DoctorProfileInDB from a raw MongoDB document (ObjectId → str)."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        # Normalise ObjectId references stored as bson.ObjectId
        if "user_id" in doc and not isinstance(doc["user_id"], str):
            doc["user_id"] = str(doc["user_id"])
        return cls(**doc)


# ---------------------------------------------------------------------------
# doctor_documents
# ---------------------------------------------------------------------------

class DoctorDocumentBase(BaseModel):
    """Base fields shared across doctor document models"""
    model_config = ConfigDict(populate_by_name=True)

    document_type: DocumentType = Field(..., description="Type of verification document")
    document_url: str = Field(..., description="Publicly accessible URL of the uploaded document")


class DoctorDocumentCreate(DoctorDocumentBase):
    """Schema used to create a new doctor document"""
    doctor_id: str = Field(..., description="Reference to the doctor profile")
    verification_status: DocumentVerificationStatus = Field(
        default=DocumentVerificationStatus.PENDING,
        description="Admin review status for the document",
    )
    uploaded_at: datetime = Field(default_factory=utc_now, description="Upload timestamp")
    verified_at: Optional[datetime] = Field(None, description="Timestamp when the document was reviewed")
    verified_by: Optional[str] = Field(None, description="Admin user ID who reviewed the document")


class DoctorDocumentUpdate(BaseModel):
    """Schema used to update an existing doctor document (all fields optional)"""
    document_type: Optional[DocumentType] = None
    document_url: Optional[str] = None
    verification_status: Optional[DocumentVerificationStatus] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None


class DoctorDocumentInDB(DoctorDocumentBase):
    """Doctor document as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    doctor_id: str = Field(..., description="Reference to the doctor profile")
    verification_status: DocumentVerificationStatus = Field(
        default=DocumentVerificationStatus.PENDING,
        description="Admin review status",
    )
    uploaded_at: datetime = Field(default_factory=utc_now, description="Upload timestamp")
    verified_at: Optional[datetime] = Field(None, description="Admin review timestamp")
    verified_by: Optional[str] = Field(None, description="Admin user ID who reviewed")

    @classmethod
    def from_mongo(cls, data: dict) -> "DoctorDocumentInDB":
        """Create DoctorDocumentInDB from a raw MongoDB document (ObjectId → str)."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("doctor_id", "verified_by"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)


# ---------------------------------------------------------------------------
# doctor_availability
# ---------------------------------------------------------------------------

class DoctorAvailabilityBase(BaseModel):
    """Base fields shared across doctor availability models"""
    model_config = ConfigDict(populate_by_name=True)

    day_of_week: DayOfWeek = Field(..., description="Day of the week for this availability slot")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Slot start time (HH:MM)")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Slot end time (HH:MM)")
    slot_duration: int = Field(default=30, ge=5, le=240, description="Duration of each appointment slot in minutes")
    active: bool = Field(default=True, description="Whether this availability is currently active")


class DoctorAvailabilityCreate(DoctorAvailabilityBase):
    """Schema used to create a new availability record"""
    doctor_id: str = Field(..., description="Reference to the doctor profile")


class DoctorAvailabilityUpdate(BaseModel):
    """Schema used to update an existing availability record (all fields optional)"""
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    slot_duration: Optional[int] = Field(None, ge=5, le=240)
    active: Optional[bool] = None


class DoctorAvailabilityInDB(DoctorAvailabilityBase):
    """Doctor availability as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    doctor_id: str = Field(..., description="Reference to the doctor profile")

    @classmethod
    def from_mongo(cls, data: dict) -> "DoctorAvailabilityInDB":
        """Create DoctorAvailabilityInDB from a raw MongoDB document (ObjectId → str)."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        if "doctor_id" in doc and not isinstance(doc["doctor_id"], str):
            doc["doctor_id"] = str(doc["doctor_id"])
        return cls(**doc)
