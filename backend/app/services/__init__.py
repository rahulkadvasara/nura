"""
Nura - Services Package
Business logic services for the application
"""

from app.services.base import BaseService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.otp_service import OTPService
from app.services.email_service import EmailService
from app.services.doctor_service import (
    DoctorProfileService,
    DoctorDocumentService,
    DoctorAvailabilityService,
)

__all__ = [
    # Base service
    "BaseService",

    # Specific services
    "UserService",
    "AuthService",
    "OTPService",
    "EmailService",

    # Doctor services
    "DoctorProfileService",
    "DoctorDocumentService",
    "DoctorAvailabilityService",
]