"""
Nura - Repositories Package
MongoDB repositories for data access
"""

from app.repositories.base import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.otp_repository import OTPRepository
from app.repositories.doctor_repository import (
    DoctorProfileRepository,
    DoctorDocumentRepository,
    DoctorAvailabilityRepository,
)
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.prescription_repository import PrescriptionRepository

__all__ = [
    # Base repository
    "BaseRepository",

    # Specific repositories
    "UserRepository",
    "RefreshTokenRepository",
    "OTPRepository",

    # Doctor repositories
    "DoctorProfileRepository",
    "DoctorDocumentRepository",
    "DoctorAvailabilityRepository",

    # Appointment repositories
    "AppointmentRepository",
    "ConsultationRepository",
    "PrescriptionRepository",
]