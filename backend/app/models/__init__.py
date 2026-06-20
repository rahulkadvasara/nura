"""
Nura - Models Package
MongoDB models for the application
"""

from app.models.user import (
    UserRole,
    AuthProvider,
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse
)

from app.models.refresh_token import (
    RefreshTokenBase,
    RefreshTokenCreate,
    RefreshTokenInDB,
    RefreshTokenResponse
)

from app.models.otp_verification import (
    OTPPurpose,
    OTPVerificationBase,
    OTPVerificationCreate,
    OTPVerificationInDB,
    OTPVerificationResponse
)

__all__ = [
    # User models
    "UserRole",
    "AuthProvider",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    
    # Refresh token models
    "RefreshTokenBase",
    "RefreshTokenCreate",
    "RefreshTokenInDB",
    "RefreshTokenResponse",
    
    # OTP verification models
    "OTPPurpose",
    "OTPVerificationBase",
    "OTPVerificationCreate",
    "OTPVerificationInDB",
    "OTPVerificationResponse",
]