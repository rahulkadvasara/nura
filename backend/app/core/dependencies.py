"""
Nura - Dependencies
Dependency injection for services and repositories
"""

from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError

from app.core.config import settings
from app.db import get_database
from app.models import UserInDB, UserRole
from app.repositories import (
    UserRepository,
    RefreshTokenRepository,
    OTPRepository,
    DoctorProfileRepository,
    DoctorDocumentRepository,
    DoctorAvailabilityRepository,
    AppointmentRepository,
    NotificationRepository,
    ConsultationRepository,
)
from app.services import (
    UserService,
    AuthService,
    OTPService,
    EmailService,
    DoctorProfileService,
    DoctorDocumentService,
    DoctorAvailabilityService,
    AppointmentService,
    NotificationService,
    ConsultationService,
)



def get_user_repository() -> UserRepository:
    """Get UserRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return UserRepository(database.users)


def get_refresh_token_repository() -> RefreshTokenRepository:
    """Get RefreshTokenRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return RefreshTokenRepository(database.refresh_tokens)


def get_otp_repository() -> OTPRepository:
    """Get OTPRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return OTPRepository(database.otp_verifications)


def get_user_service() -> UserService:
    """Get UserService instance"""
    user_repository = get_user_repository()
    return UserService(user_repository)


def get_auth_service() -> AuthService:
    """Get AuthService instance"""
    user_service = get_user_service()
    refresh_token_repository = get_refresh_token_repository()
    return AuthService(user_service, refresh_token_repository)


def get_otp_service() -> OTPService:
    """Get OTPService instance"""
    otp_repository = get_otp_repository()
    return OTPService(otp_repository)


def get_email_service() -> EmailService:
    """Get EmailService instance"""
    return EmailService()


def get_doctor_profile_repository() -> DoctorProfileRepository:
    """Get DoctorProfileRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return DoctorProfileRepository(database.doctor_profiles)


def get_doctor_document_repository() -> DoctorDocumentRepository:
    """Get DoctorDocumentRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return DoctorDocumentRepository(database.doctor_documents)


def get_doctor_profile_service() -> DoctorProfileService:
    """Get DoctorProfileService instance"""
    profile_repository = get_doctor_profile_repository()
    user_repository = get_user_repository()
    return DoctorProfileService(profile_repository, user_repository)


def get_doctor_document_service() -> DoctorDocumentService:
    """Get DoctorDocumentService instance"""
    document_repository = get_doctor_document_repository()
    return DoctorDocumentService(document_repository)


def get_notification_repository() -> NotificationRepository:
    """Get NotificationRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return NotificationRepository(database.notifications)


def get_notification_service(
    notification_repository: NotificationRepository = Depends(get_notification_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> NotificationService:
    """Get NotificationService instance"""
    return NotificationService(notification_repository, user_repository)


def get_doctor_availability_repository() -> DoctorAvailabilityRepository:
    """Get DoctorAvailabilityRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return DoctorAvailabilityRepository(database.doctor_availability)


def get_doctor_availability_service(
    availability_repository: DoctorAvailabilityRepository = Depends(get_doctor_availability_repository)
) -> DoctorAvailabilityService:
    """Get DoctorAvailabilityService instance"""
    database: AsyncIOMotorDatabase = get_database()
    from app.repositories.appointment_repository import AppointmentRepository
    appointment_repository = AppointmentRepository(database.appointments)
    return DoctorAvailabilityService(availability_repository, appointment_repository)


def get_appointment_repository() -> AppointmentRepository:
    """Get AppointmentRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return AppointmentRepository(database.appointments)


def get_appointment_service(
    appointment_repository: AppointmentRepository = Depends(get_appointment_repository),
    doctor_profile_repository: DoctorProfileRepository = Depends(get_doctor_profile_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    doctor_availability_repository: DoctorAvailabilityRepository = Depends(get_doctor_availability_repository),
) -> AppointmentService:
    """Get AppointmentService instance"""
    return AppointmentService(
        appointment_repository=appointment_repository,
        doctor_profile_repository=doctor_profile_repository,
        user_repository=user_repository,
        doctor_availability_repository=doctor_availability_repository,
    )


def get_consultation_repository() -> ConsultationRepository:
    """Get ConsultationRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return ConsultationRepository(database.consultations)


def get_consultation_service(
    consultation_repository: ConsultationRepository = Depends(get_consultation_repository),
    appointment_repository: AppointmentRepository = Depends(get_appointment_repository),
) -> ConsultationService:
    """Get ConsultationService instance"""
    return ConsultationService(consultation_repository, appointment_repository)


def get_audit_log_repository():
    """Get AuditLogRepository instance"""
    from app.repositories.audit_log_repository import AuditLogRepository
    database = get_database()
    return AuditLogRepository(database.audit_logs)


def get_audit_log_service():
    """Get AuditLogService instance"""
    from app.services.audit_log_service import AuditLogService
    audit_log_repository = get_audit_log_repository()
    user_repository = get_user_repository()
    return AuditLogService(audit_log_repository, user_repository)


reusable_oauth2 = HTTPBearer()


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserInDB:
    """Validate JWT access token and return the user"""
    try:
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Enforce active and email-verified user"""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


def require_role(required_role: UserRole):
    """Enforce specific user role (admin > doctor > patient)"""
    def dependency(
        current_user: UserInDB = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> UserInDB:
        try:
            auth_service.require_role(current_user, required_role)
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        return current_user
    return dependency


async def require_verified_doctor(
    current_user: UserInDB = Depends(require_role(UserRole.DOCTOR)),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
):
    """Enforce that current user is a verified doctor (role is exactly doctor and profile verified)"""
    from app.models.doctor import DoctorProfileStatus, DoctorProfileInDB
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only verified doctors can manage availability"
        )
    profile = await doctor_profile_service.get_profile_by_user_id(current_user.id)
    if not profile or profile.profile_status != DoctorProfileStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor profile must be verified to manage availability"
        )
    return profile


# ---------------------------------------------------------------------------
# Dashboard service dependency factories
# ---------------------------------------------------------------------------

def get_patient_dashboard_service():
    """Get PatientDashboardService instance"""
    from app.services.patient_dashboard_service import PatientDashboardService
    from app.repositories.appointment_repository import AppointmentRepository
    from app.repositories.reminder_repository import ReminderRepository
    from app.repositories.report_repository import ReportRepository
    from app.repositories.notification_repository import NotificationRepository
    from app.repositories.health_insight_repository import HealthInsightRepository

    database = get_database()
    return PatientDashboardService(
        appointment_repository=AppointmentRepository(database.appointments),
        reminder_repository=ReminderRepository(database.reminders),
        report_repository=ReportRepository(database.reports),
        notification_repository=NotificationRepository(database.notifications),
        health_insight_repository=HealthInsightRepository(database.health_insights),
    )


def get_doctor_dashboard_service():
    """Get DoctorDashboardService instance"""
    from app.services.doctor_dashboard_service import DoctorDashboardService
    from app.repositories.appointment_repository import AppointmentRepository
    from app.repositories.doctor_wallet_repository import DoctorWalletRepository
    from app.repositories.doctor_repository import DoctorProfileRepository, DoctorDocumentRepository

    database = get_database()
    return DoctorDashboardService(
        appointment_repository=AppointmentRepository(database.appointments),
        doctor_wallet_repository=DoctorWalletRepository(database.doctor_wallets),
        doctor_profile_repository=DoctorProfileRepository(database.doctor_profiles),
        doctor_document_repository=DoctorDocumentRepository(database.doctor_documents),
    )



def get_admin_dashboard_service():
    """Get AdminDashboardService instance"""
    from app.services.admin_dashboard_service import AdminDashboardService
    from app.repositories.user_repository import UserRepository
    from app.repositories.appointment_repository import AppointmentRepository
    from app.repositories.consultation_repository import ConsultationRepository
    from app.repositories.payment_repository import PaymentRepository
    from app.repositories.doctor_repository import DoctorProfileRepository
    from app.repositories.report_repository import ReportRepository
    from app.repositories.reminder_repository import ReminderRepository
    from app.repositories.chat_session_repository import ChatSessionRepository

    database = get_database()
    return AdminDashboardService(
        user_repository=UserRepository(database.users),
        appointment_repository=AppointmentRepository(database.appointments),
        consultation_repository=ConsultationRepository(database.consultations),
        payment_repository=PaymentRepository(database.payments),
        doctor_profile_repository=DoctorProfileRepository(database.doctor_profiles),
        report_repository=ReportRepository(database.reports),
        reminder_repository=ReminderRepository(database.reminders),
        chat_session_repository=ChatSessionRepository(database.chat_sessions),
    )

