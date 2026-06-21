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

from app.schemas.appointment import (
    # Appointment schemas
    AppointmentCreateSchema,
    AppointmentUpdateSchema,
    AppointmentResponse,
    # Consultation schemas
    ConsultationCreateSchema,
    ConsultationUpdateSchema,
    ConsultationResponse,
    # Prescription schemas
    MedicationSchema,
    PrescriptionCreateSchema,
    PrescriptionUpdateSchema,
    PrescriptionResponse,
)

from app.schemas.report import (
    # Report schemas
    ReportCreateSchema,
    ReportUpdateSchema,
    ReportResponse,
    # Health Insight schemas
    HealthInsightCreateSchema,
    HealthInsightUpdateSchema,
    HealthInsightResponse,
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

    # Appointment schemas
    "AppointmentCreateSchema",
    "AppointmentUpdateSchema",
    "AppointmentResponse",

    # Consultation schemas
    "ConsultationCreateSchema",
    "ConsultationUpdateSchema",
    "ConsultationResponse",

    # Prescription schemas
    "MedicationSchema",
    "PrescriptionCreateSchema",
    "PrescriptionUpdateSchema",
    "PrescriptionResponse",

    # Report & Health Insight schemas
    "ReportCreateSchema",
    "ReportUpdateSchema",
    "ReportResponse",
    "HealthInsightCreateSchema",
    "HealthInsightUpdateSchema",
    "HealthInsightResponse",
]