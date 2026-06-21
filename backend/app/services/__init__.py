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
]