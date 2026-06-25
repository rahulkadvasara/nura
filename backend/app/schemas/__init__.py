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
    ErrorResponse,
    ChangePasswordRequest
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
    # Admin verification schemas
    AdminDoctorListResponse,
    DoctorVerificationResponse,
    DoctorApprovalRequest,
    DoctorRejectionRequest,
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

from app.schemas.reminder import (
    ReminderCreateSchema,
    ReminderUpdateSchema,
    ReminderResponse,
)

from app.schemas.notification import (
    NotificationCreateSchema,
    NotificationUpdateSchema,
    NotificationResponse,
)

from app.schemas.chat import (
    ChatMessageMetadata,
    ChatSessionCreateSchema,
    ChatSessionUpdateSchema,
    ChatSessionResponse,
    ChatMessageCreateSchema,
    ChatMessageUpdateSchema,
    ChatMessageResponse,
)

from app.schemas.payment import (
    PaymentCreateSchema,
    PaymentUpdateSchema,
    PaymentResponse,
    DoctorWalletCreateSchema,
    DoctorWalletUpdateSchema,
    DoctorWalletResponse,
)

from app.schemas.observability import (
    AgentLogCreateSchema,
    AgentLogUpdateSchema,
    AgentLogResponse,
    AuditLogCreateSchema,
    AuditLogUpdateSchema,
    AuditLogResponse,
)

from app.schemas.dashboard import (
    RecentHealthInsight,
    PatientDashboardResponse,
    DoctorDashboardResponse,
    AdminDashboardResponse,
)

from app.schemas.admin import (
    AdminCreateRequest,
    AdminCreateResponse,
    AdminDetailResponse,
)

from app.schemas.doctor_patient import (
    DoctorPatientSummary,
    DoctorPatientListResponse,
    DoctorPatientDetailResponse,
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
    "ChangePasswordRequest",


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

    # Admin verification schemas
    "AdminDoctorListResponse",
    "DoctorVerificationResponse",
    "DoctorApprovalRequest",
    "DoctorRejectionRequest",

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

    # Reminder schemas
    "ReminderCreateSchema",
    "ReminderUpdateSchema",
    "ReminderResponse",

    # Notification schemas
    "NotificationCreateSchema",
    "NotificationUpdateSchema",
    "NotificationResponse",

    # Chat schemas
    "ChatMessageMetadata",
    "ChatSessionCreateSchema",
    "ChatSessionUpdateSchema",
    "ChatSessionResponse",
    "ChatMessageCreateSchema",
    "ChatMessageUpdateSchema",
    "ChatMessageResponse",

    # Payment and doctor wallet schemas
    "PaymentCreateSchema",
    "PaymentUpdateSchema",
    "PaymentResponse",
    "DoctorWalletCreateSchema",
    "DoctorWalletUpdateSchema",
    "DoctorWalletResponse",

    # Observability and audit schemas
    "AgentLogCreateSchema",
    "AgentLogUpdateSchema",
    "AgentLogResponse",
    "AuditLogCreateSchema",
    "AuditLogUpdateSchema",
    "AuditLogResponse",

    # Dashboard response schemas
    "RecentHealthInsight",
    "PatientDashboardResponse",
    "DoctorDashboardResponse",
    "AdminDashboardResponse",

    # Admin Management schemas
    "AdminCreateRequest",
    "AdminCreateResponse",
    "AdminDetailResponse",

    # Doctor Patient Management schemas
    "DoctorPatientSummary",
    "DoctorPatientListResponse",
    "DoctorPatientDetailResponse",
]