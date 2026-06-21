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

from app.models.report import (
    ReportType,
    ProcessingStatus,
    RiskLevel,
    InsightType,
    Severity,
    ReportBase,
    ReportCreate,
    ReportUpdate,
    ReportInDB,
    HealthInsightBase,
    HealthInsightCreate,
    HealthInsightUpdate,
    HealthInsightInDB,
)

from app.models.preferences import (
    NotificationPreferencesBase,
    NotificationPreferencesUpdate,
    NotificationPreferencesInDB,
    NotificationPreferencesResponse,
)

from app.models.reminder import (
    ReminderType,
    ReminderStatus,
    ReminderSourceType,
    ReminderInDB,
)

from app.models.notification import (
    NotificationType,
    NotificationPriority,
    NotificationInDB,
)

from app.models.chat import (
    SessionType,
    SenderType,
    MessageType,
    ChatSessionBase,
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionInDB,
    ChatMessageBase,
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageInDB,
)

from app.models.payment import (
    PaymentStatus,
    PaymentMethod,
    PaymentBase,
    PaymentCreate,
    PaymentUpdate,
    PaymentInDB,
    DoctorWalletBase,
    DoctorWalletCreate,
    DoctorWalletUpdate,
    DoctorWalletInDB,
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

    # Report & Health Insight models
    "ReportType",
    "ProcessingStatus",
    "RiskLevel",
    "InsightType",
    "Severity",
    "ReportBase",
    "ReportCreate",
    "ReportUpdate",
    "ReportInDB",
    "HealthInsightBase",
    "HealthInsightCreate",
    "HealthInsightUpdate",
    "HealthInsightInDB",

    # Reminder & Notification models
    "ReminderType",
    "ReminderStatus",
    "ReminderSourceType",
    "ReminderInDB",
    "NotificationType",
    "NotificationPriority",
    "NotificationInDB",

    # Chat session and message models
    "SessionType",
    "SenderType",
    "MessageType",
    "ChatSessionBase",
    "ChatSessionCreate",
    "ChatSessionUpdate",
    "ChatSessionInDB",
    "ChatMessageBase",
    "ChatMessageCreate",
    "ChatMessageUpdate",
    "ChatMessageInDB",

    # Payment and doctor wallet models
    "PaymentStatus",
    "PaymentMethod",
    "PaymentBase",
    "PaymentCreate",
    "PaymentUpdate",
    "PaymentInDB",
    "DoctorWalletBase",
    "DoctorWalletCreate",
    "DoctorWalletUpdate",
    "DoctorWalletInDB",
]