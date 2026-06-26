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
from app.services.admin_analytics_service import AdminAnalyticsService
from app.services.doctor_patient_service import DoctorPatientService
from app.services.doctor_earnings_service import DoctorEarningsService
from app.services.payment_gateway_service import PaymentGatewayService
from app.services.groq_service import GroqService, get_groq_service
from app.services.ai_service import AIService, get_ai_service
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.vector_collection_service import VectorCollectionService, get_vector_collection_service
from app.services.vector_service import VectorService, get_vector_service
from app.services.patient_context_service import PatientContextService
from app.services.ai_orchestrator import AIOrchestrator
from app.services.index_version_service import IndexVersionService, get_index_version_service
from app.services.document_metadata_service import DocumentMetadataService, get_document_metadata_service
from app.services.document_indexing_service import DocumentIndexingService, get_document_indexing_service
from app.services.retrieval_service import RetrievalService, get_retrieval_service


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
    "PaymentGatewayService",

    # Observability and audit services
    "AgentLogService",
    "AuditLogService",

    # Dashboard aggregation services
    "PatientDashboardService",
    "DoctorDashboardService",
    "AdminDashboardService",
    "AdminAnalyticsService",

    # Doctor Patient Management service
    "DoctorPatientService",

    # Doctor Earnings & Wallet service
    "DoctorEarningsService",

    # AI services
    "GroqService",
    "get_groq_service",
    "AIService",
    "get_ai_service",
    "EmbeddingService",
    "get_embedding_service",
    "VectorCollectionService",
    "get_vector_collection_service",
    "VectorService",
    "get_vector_service",
    "PatientContextService",
    "AIOrchestrator",
    "IndexVersionService",
    "get_index_version_service",
    "DocumentMetadataService",
    "get_document_metadata_service",
    "DocumentIndexingService",
    "get_document_indexing_service",
    "RetrievalService",
    "get_retrieval_service",
]