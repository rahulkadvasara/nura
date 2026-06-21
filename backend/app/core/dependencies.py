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
from app.repositories import UserRepository, RefreshTokenRepository, OTPRepository
from app.services import UserService, AuthService, OTPService, EmailService



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

    database = get_database()
    return DoctorDashboardService(
        appointment_repository=AppointmentRepository(database.appointments),
        doctor_wallet_repository=DoctorWalletRepository(database.doctor_wallets),
    )


def get_admin_dashboard_service():
    """Get AdminDashboardService instance"""
    from app.services.admin_dashboard_service import AdminDashboardService
    from app.repositories.user_repository import UserRepository
    from app.repositories.appointment_repository import AppointmentRepository
    from app.repositories.consultation_repository import ConsultationRepository
    from app.repositories.payment_repository import PaymentRepository
    from app.repositories.doctor_repository import DoctorProfileRepository

    database = get_database()
    return AdminDashboardService(
        user_repository=UserRepository(database.users),
        appointment_repository=AppointmentRepository(database.appointments),
        consultation_repository=ConsultationRepository(database.consultations),
        payment_repository=PaymentRepository(database.payments),
        doctor_profile_repository=DoctorProfileRepository(database.doctor_profiles),
    )
