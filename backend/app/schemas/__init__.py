"""
Nura - Schemas Package
Pydantic schemas for API requests and responses
"""

from app.schemas.auth import (
    UserLogin,
    OTPCreate,
    OTPVerify,
    TokenResponse,
    RefreshTokenRequest,
    TokenUser,
    SuccessResponse,
    ErrorResponse
)

from app.schemas.doctor import (
    # Doctor profile schemas
    DoctorProfileCreateSchema,
    DoctorProfileUpdateSchema,
    DoctorProfileResponse,
    # Doctor document schemas
    DoctorDocumentCreateSchema,
    DoctorDocumentUpdateSchema,
    DoctorDocumentResponse,
    # Doctor availability schemas
    DoctorAvailabilityCreateSchema,
    DoctorAvailabilityUpdateSchema,
    DoctorAvailabilityResponse,
)

__all__ = [
    # Authentication schemas
    "UserLogin",
    "OTPCreate",
    "OTPVerify",
    "TokenResponse",
    "RefreshTokenRequest",
    "TokenUser",
    "SuccessResponse",
    "ErrorResponse",

    # Doctor profile schemas
    "DoctorProfileCreateSchema",
    "DoctorProfileUpdateSchema",
    "DoctorProfileResponse",

    # Doctor document schemas
    "DoctorDocumentCreateSchema",
    "DoctorDocumentUpdateSchema",
    "DoctorDocumentResponse",

    # Doctor availability schemas
    "DoctorAvailabilityCreateSchema",
    "DoctorAvailabilityUpdateSchema",
    "DoctorAvailabilityResponse",
]