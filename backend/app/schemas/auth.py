"""
Nura - Authentication Schemas
Pydantic v2 schemas for authentication API requests and responses
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from app.models import UserRole, AuthProvider


class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower().strip()


class OTPCreate(BaseModel):
    """OTP creation request schema"""
    email: EmailStr = Field(..., description="Email address for OTP")
    purpose: str = Field(..., description="Purpose of OTP (registration or password_reset)")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower().strip()

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """Validate OTP purpose"""
        valid_purposes = {"registration", "password_reset"}
        if v not in valid_purposes:
            raise ValueError(f"Purpose must be one of: {', '.join(sorted(valid_purposes))}")
        return v


class OTPVerify(BaseModel):
    """OTP verification request schema"""
    email: EmailStr = Field(..., description="Email address for verification")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower().strip()


class TokenUser(BaseModel):
    """User information embedded in a token response"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="Full name")
    email_verified: bool = Field(..., description="Email verification status")


class TokenResponse(BaseModel):
    """Token response schema"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: TokenUser = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token")


class SuccessResponse(BaseModel):
    """Generic success response schema"""
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = Field(default=False, description="Success status")
    message: str = Field(..., description="Error message")
    errors: Optional[list] = Field(None, description="Detailed error messages")


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema"""
    email: EmailStr = Field(..., description="User email address")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower().strip()


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    email: EmailStr = Field(..., description="User email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower().strip()

    @field_validator("new_password")
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
