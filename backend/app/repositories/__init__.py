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
from app.repositories.report_repository import ReportRepository
from app.repositories.health_insight_repository import HealthInsightRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.doctor_wallet_repository import DoctorWalletRepository
from app.repositories.agent_log_repository import AgentLogRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.patient_memory_repository import PatientMemoryRepository

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

    # Report & Health Insight repositories
    "ReportRepository",
    "HealthInsightRepository",

    # Reminder & Notification repositories
    "ReminderRepository",
    "NotificationRepository",

    # Chat session and message repositories
    "ChatSessionRepository",
    "ChatMessageRepository",

    # Payment and doctor wallet repositories
    "PaymentRepository",
    "DoctorWalletRepository",

    # Observability and audit repositories
    "AgentLogRepository",
    "AuditLogRepository",

    # Patient memory repositories
    "PatientMemoryRepository",
]