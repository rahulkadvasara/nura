"""
Nura - OTP Verification Model
MongoDB model for OTP-based verification
"""

from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class OTPPurpose(str, Enum):
    """OTP purpose enumeration"""
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"


class OTPVerificationBase(BaseModel):
    """Base OTP verification model"""
    email: EmailStr = Field(..., description="Email address for verification")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")
    purpose: OTPPurpose = Field(..., description="Purpose of OTP")
    expires_at: datetime = Field(..., description="OTP expiration timestamp")
    verified: bool = Field(default=False, description="Verification status")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower().strip()


class OTPVerificationCreate(OTPVerificationBase):
    """OTP verification creation model"""
    pass


class OTPVerificationInDB(OTPVerificationBase):
    """OTP verification model as stored in database"""
    id: str = Field(..., description="OTP verification ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "OTPVerificationInDB":
        """Create OTPVerificationInDB from a raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)


class OTPVerificationResponse(BaseModel):
    """OTP verification response model"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

    id: str = Field(..., description="OTP verification ID")
    email: EmailStr = Field(..., description="Email address for verification")
    purpose: OTPPurpose = Field(..., description="Purpose of OTP")
    expires_at: datetime = Field(..., description="OTP expiration timestamp")
    verified: bool = Field(..., description="Verification status")
    created_at: datetime = Field(..., description="Creation timestamp")
