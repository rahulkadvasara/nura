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
from app.services.appointment_service import AppointmentService
from app.services.consultation_service import ConsultationService
from app.services.prescription_service import PrescriptionService
from app.services.report_service import ReportService
from app.services.health_insight_service import HealthInsightService
from app.services.reminder_service import ReminderService
from app.services.notification_service import NotificationService
from app.services.chat_session_service import ChatSessionService
from app.services.chat_message_service import ChatMessageService
from app.services.payment_service import PaymentService
from app.services.doctor_wallet_service import DoctorWalletService
from app.services.agent_log_service import AgentLogService
from app.services.audit_log_service import AuditLogService
from app.services.patient_dashboard_service import PatientDashboardService
from app.services.doctor_dashboard_service import DoctorDashboardService
from app.services.admin_dashboard_service import AdminDashboardService
from app.services.admin_bootstrap_service import AdminBootstrapService

__all__ = [
    # Base service
    "BaseService",

    # Specific services
    "UserService",
    "AuthService",
    "OTPService",
    "EmailService",
    "AdminBootstrapService",

    # Doctor services
    "DoctorProfileService",
    "DoctorDocumentService",
    "DoctorAvailabilityService",

    # Appointment services
    "AppointmentService",
    "ConsultationService",
    "PrescriptionService",

    # Report & Health Insight services
    "ReportService",
    "HealthInsightService",

    # Reminder & Notification services
    "ReminderService",
    "NotificationService",

    # Chat session and message services
    "ChatSessionService",
    "ChatMessageService",

    # Payment and doctor wallet services
    "PaymentService",
    "DoctorWalletService",

    # Observability and audit services
    "AgentLogService",
    "AuditLogService",

    # Dashboard aggregation services
    "PatientDashboardService",
    "DoctorDashboardService",
    "AdminDashboardService",
]