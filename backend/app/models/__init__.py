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

from app.models.doctor import (
    # Enumerations
    DoctorProfileStatus,
    DocumentType,
    DocumentVerificationStatus,
    DayOfWeek,
    # Doctor profile models
    DoctorProfileBase,
    DoctorProfileCreate,
    DoctorProfileUpdate,
    DoctorProfileInDB,
    # Doctor document models
    DoctorDocumentBase,
    DoctorDocumentCreate,
    DoctorDocumentUpdate,
    DoctorDocumentInDB,
    # Doctor availability models
    DoctorAvailabilityBase,
    DoctorAvailabilityCreate,
    DoctorAvailabilityUpdate,
    DoctorAvailabilityInDB,
)

from app.models.appointment import (
    AppointmentStatus,
    PaymentStatus,
    AppointmentBase,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentInDB,
    ConsultationBase,
    ConsultationCreate,
    ConsultationUpdate,
    ConsultationInDB,
    Medication,
    PrescriptionBase,
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionInDB,
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

    # Doctor enumerations
    "DoctorProfileStatus",
    "DocumentType",
    "DocumentVerificationStatus",
    "DayOfWeek",

    # Doctor profile models
    "DoctorProfileBase",
    "DoctorProfileCreate",
    "DoctorProfileUpdate",
    "DoctorProfileInDB",

    # Doctor document models
    "DoctorDocumentBase",
    "DoctorDocumentCreate",
    "DoctorDocumentUpdate",
    "DoctorDocumentInDB",

    # Doctor availability models
    "DoctorAvailabilityBase",
    "DoctorAvailabilityCreate",
    "DoctorAvailabilityUpdate",
    "DoctorAvailabilityInDB",

    # Appointment, Consultation, Prescription models
    "AppointmentStatus",
    "PaymentStatus",
    "AppointmentBase",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentInDB",
    "ConsultationBase",
    "ConsultationCreate",
    "ConsultationUpdate",
    "ConsultationInDB",
    "Medication",
    "PrescriptionBase",
    "PrescriptionCreate",
    "PrescriptionUpdate",
    "PrescriptionInDB",
]