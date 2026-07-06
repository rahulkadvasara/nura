"""
Nura - User Model
MongoDB model for user authentication and profile
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator, model_serializer, ConfigDict
from app.models.storage import FileMetadata


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    """User role enumeration"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class AuthProvider(str, Enum):
    """Authentication provider enumeration"""
    LOCAL = "local"
    GOOGLE = "google"


class UserBase(BaseModel):
    """Base user model with common fields"""
    model_config = ConfigDict(populate_by_name=True)

    role: UserRole = Field(default=UserRole.PATIENT, description="User role")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    profile_picture_metadata: Optional[FileMetadata] = Field(None, description="Avatar storage metadata")
    auth_provider: AuthProvider = Field(default=AuthProvider.LOCAL, description="Authentication provider")
    email_verified: bool = Field(default=False, description="Email verification status")
    is_active: bool = Field(default=True, description="Account active status")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower().strip()


class UserCreate(UserBase):
    """User creation model with password"""
    password: str = Field(..., min_length=8, description="User password")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    profile_picture_metadata: Optional[FileMetadata] = Field(None, description="Avatar storage metadata")
    is_active: Optional[bool] = Field(None, description="Account active status")
    password_hash: Optional[str] = Field(None, description="Hashed password (internal use only)")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")


class UserInDB(UserBase):
    """User model as stored in database"""
    id: str = Field(..., description="User ID")
    password_hash: str = Field(..., description="Hashed password")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "UserInDB":
        """Create UserInDB from a raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)


class UserResponse(BaseModel):
    """User response model for API responses"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

    id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    profile_picture_metadata: Optional[FileMetadata] = Field(None, description="Avatar storage metadata")
    auth_provider: AuthProvider = Field(..., description="Authentication provider")
    email_verified: bool = Field(..., description="Email verification status")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
