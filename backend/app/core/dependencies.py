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
    PrescriptionRepository,
    PaymentRepository,
    DoctorWalletRepository,
    PatientMemoryRepository,
    ReportRepository,
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
    PrescriptionService,
    PaymentService,
    PaymentGatewayService,
    GroqService,
    AIService,
    EmbeddingService,
    VectorCollectionService,
    VectorService,
    PatientContextService,
    AIOrchestrator,
    IndexVersionService,
    DocumentMetadataService,
    DocumentIndexingService,
    RetrievalService,
    ContextAssemblyService,
    IntentDetectionService,
    get_intent_detection_service,
    PatientSummaryBuilder,
    MemorySyncService,
    ReminderService,
)
from app.events import EventDispatcher, EventQueue
from app.agents import (
    BaseAgent,
    RetrievalAgent,
    MemoryAgent,
    MedicalKnowledgeAgent,
    SymptomAgent,
    ReportAnalysisAgent,
    DrugInteractionAgent,
    DoctorRecommendationAgent,
    ReminderAgent,
    AppointmentAgent,
)
from app.prompts.loader import PromptLoader




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


def get_prescription_repository() -> PrescriptionRepository:
    """Get PrescriptionRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return PrescriptionRepository(database.prescriptions)


def get_prescription_service(
    prescription_repository: PrescriptionRepository = Depends(get_prescription_repository),
    consultation_repository: ConsultationRepository = Depends(get_consultation_repository),
) -> PrescriptionService:
    """Get PrescriptionService instance"""
    return PrescriptionService(prescription_repository, consultation_repository)


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


def get_payment_repository() -> PaymentRepository:
    """Get PaymentRepository instance"""
    database = get_database()
    return PaymentRepository(database.payments)


def get_doctor_wallet_repository() -> DoctorWalletRepository:
    """Get DoctorWalletRepository instance"""
    database = get_database()
    return DoctorWalletRepository(database.doctor_wallets)


def get_payment_service(
    payment_repository: PaymentRepository = Depends(get_payment_repository),
    appointment_repository: AppointmentRepository = Depends(get_appointment_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    doctor_profile_repository: DoctorProfileRepository = Depends(get_doctor_profile_repository),
    audit_log_service = Depends(get_audit_log_service),
) -> PaymentService:
    """Get PaymentService instance"""
    return PaymentService(
        payment_repository=payment_repository,
        appointment_repository=appointment_repository,
        user_repository=user_repository,
        doctor_profile_repository=doctor_profile_repository,
        audit_log_service=audit_log_service,
    )



def get_payment_gateway_service(
    payment_repository: PaymentRepository = Depends(get_payment_repository),
    appointment_repository: AppointmentRepository = Depends(get_appointment_repository),
    doctor_profile_repository: DoctorProfileRepository = Depends(get_doctor_profile_repository),
    doctor_wallet_repository: DoctorWalletRepository = Depends(get_doctor_wallet_repository),
    notification_service: NotificationService = Depends(get_notification_service),
    user_repository: UserRepository = Depends(get_user_repository),
    audit_log_service = Depends(get_audit_log_service),
) -> PaymentGatewayService:
    """Get PaymentGatewayService instance"""
    return PaymentGatewayService(
        payment_repository=payment_repository,
        appointment_repository=appointment_repository,
        doctor_profile_repository=doctor_profile_repository,
        doctor_wallet_repository=doctor_wallet_repository,
        notification_service=notification_service,
        user_repository=user_repository,
        audit_log_service=audit_log_service,
    )


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


def require_exact_patient(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Enforce that the logged-in user has exactly the PATIENT role."""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients are permitted to access this resource",
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
    from app.repositories.consultation_repository import ConsultationRepository
    from app.repositories.prescription_repository import PrescriptionRepository
    from app.repositories.doctor_repository import DoctorProfileRepository
    from app.repositories.user_repository import UserRepository

    database = get_database()
    return PatientDashboardService(
        appointment_repository=AppointmentRepository(database.appointments),
        reminder_repository=ReminderRepository(database.reminders),
        report_repository=ReportRepository(database.reports),
        notification_repository=NotificationRepository(database.notifications),
        health_insight_repository=HealthInsightRepository(database.health_insights),
        consultation_repository=ConsultationRepository(database.consultations),
        prescription_repository=PrescriptionRepository(database.prescriptions),
        doctor_profile_repository=DoctorProfileRepository(database.doctor_profiles),
        user_repository=UserRepository(database.users),
    )


def get_doctor_dashboard_service():
    """Get DoctorDashboardService instance"""
    from app.services.doctor_dashboard_service import DoctorDashboardService
    from app.repositories.appointment_repository import AppointmentRepository
    from app.repositories.doctor_wallet_repository import DoctorWalletRepository
    from app.repositories.doctor_repository import DoctorProfileRepository, DoctorDocumentRepository
    from app.repositories.prescription_repository import PrescriptionRepository

    database = get_database()
    return DoctorDashboardService(
        appointment_repository=AppointmentRepository(database.appointments),
        doctor_wallet_repository=DoctorWalletRepository(database.doctor_wallets),
        doctor_profile_repository=DoctorProfileRepository(database.doctor_profiles),
        doctor_document_repository=DoctorDocumentRepository(database.doctor_documents),
        prescription_repository=PrescriptionRepository(database.prescriptions),
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


def get_admin_analytics_service():
    """Get AdminAnalyticsService instance"""
    from app.services.admin_analytics_service import AdminAnalyticsService
    from app.repositories.user_repository import UserRepository
    from app.repositories.doctor_repository import DoctorProfileRepository, DoctorAvailabilityRepository
    from app.repositories.appointment_repository import AppointmentRepository
    from app.repositories.payment_repository import PaymentRepository
    from app.repositories.consultation_repository import ConsultationRepository
    from app.repositories.report_repository import ReportRepository
    from app.repositories.prescription_repository import PrescriptionRepository
    from app.repositories.reminder_repository import ReminderRepository

    database = get_database()
    return AdminAnalyticsService(
        user_repository=UserRepository(database.users),
        doctor_profile_repository=DoctorProfileRepository(database.doctor_profiles),
        doctor_availability_repository=DoctorAvailabilityRepository(database.doctor_availability),
        appointment_repository=AppointmentRepository(database.appointments),
        payment_repository=PaymentRepository(database.payments),
        consultation_repository=ConsultationRepository(database.consultations),
        report_repository=ReportRepository(database.reports),
        prescription_repository=PrescriptionRepository(database.prescriptions),
        reminder_repository=ReminderRepository(database.reminders),
    )


def get_doctor_patient_service():
    """Get DoctorPatientService instance"""
    from app.services.doctor_patient_service import DoctorPatientService
    from app.repositories.user_repository import UserRepository
    from app.repositories.doctor_repository import DoctorProfileRepository
    from app.repositories.appointment_repository import AppointmentRepository
    from app.repositories.consultation_repository import ConsultationRepository
    from app.repositories.prescription_repository import PrescriptionRepository
    from app.repositories.report_repository import ReportRepository
    from app.repositories.health_insight_repository import HealthInsightRepository
    from app.repositories.reminder_repository import ReminderRepository
    from app.repositories.chat_session_repository import ChatSessionRepository

    database = get_database()
    return DoctorPatientService(
        user_repository=UserRepository(database.users),
        doctor_profile_repository=DoctorProfileRepository(database.doctor_profiles),
        appointment_repository=AppointmentRepository(database.appointments),
        consultation_repository=ConsultationRepository(database.consultations),
        prescription_repository=PrescriptionRepository(database.prescriptions),
        report_repository=ReportRepository(database.reports),
        health_insight_repository=HealthInsightRepository(database.health_insights),
        reminder_repository=ReminderRepository(database.reminders),
        chat_session_repository=ChatSessionRepository(database.chat_sessions),
    )


def get_doctor_earnings_service():
    """Get DoctorEarningsService instance"""
    from app.services.doctor_earnings_service import DoctorEarningsService
    from app.repositories.doctor_wallet_repository import DoctorWalletRepository
    from app.repositories.payment_repository import PaymentRepository
    from app.repositories.appointment_repository import AppointmentRepository
    from app.repositories.user_repository import UserRepository

    database = get_database()
    return DoctorEarningsService(
        doctor_wallet_repository=DoctorWalletRepository(database.doctor_wallets),
        payment_repository=PaymentRepository(database.payments),
        appointment_repository=AppointmentRepository(database.appointments),
        user_repository=UserRepository(database.users)
    )


def get_agent_log_repository():
    """Get AgentLogRepository instance"""
    from app.repositories.agent_log_repository import AgentLogRepository
    database = get_database()
    return AgentLogRepository(database.agent_logs)


def get_agent_log_service():
    """Get AgentLogService instance"""
    from app.services.agent_log_service import AgentLogService
    agent_log_repository = get_agent_log_repository()
    return AgentLogService(agent_log_repository)


def get_system_monitor_service():
    """Get SystemMonitorService instance"""
    from app.services.system_monitor_service import SystemMonitorService
    from app.repositories.reminder_repository import ReminderRepository
    database = get_database()
    return SystemMonitorService(
        reminder_repository=ReminderRepository(database.reminders)
    )


def get_maintenance_service():
    """Get MaintenanceService instance"""
    from app.services.maintenance_service import MaintenanceService
    from app.repositories.refresh_token_repository import RefreshTokenRepository
    from app.repositories.otp_repository import OTPRepository
    from app.repositories.notification_repository import NotificationRepository
    from app.repositories.audit_log_repository import AuditLogRepository
    database = get_database()
    return MaintenanceService(
        refresh_token_repository=RefreshTokenRepository(database.refresh_tokens),
        otp_repository=OTPRepository(database.otp_verifications),
        notification_repository=NotificationRepository(database.notifications),
        audit_log_repository=AuditLogRepository(database.audit_logs),
    )


def get_groq_service() -> GroqService:
    """Get GroqService instance"""
    from app.services.groq_service import get_groq_service as get_groq_service_impl
    return get_groq_service_impl()


def get_ai_service(
    groq_service = Depends(get_groq_service)
) -> AIService:
    """Get AIService instance"""
    from app.services.ai_service import get_ai_service as get_ai_service_impl
    return get_ai_service_impl(groq_service)


def get_embedding_service() -> EmbeddingService:
    """Get EmbeddingService instance"""
    from app.services.embedding_service import get_embedding_service as get_embedding_service_impl
    return get_embedding_service_impl()


def get_vector_collection_service() -> VectorCollectionService:
    """Get VectorCollectionService instance"""
    from app.services.vector_collection_service import get_vector_collection_service as get_vector_collection_service_impl
    return get_vector_collection_service_impl()


def get_vector_service() -> VectorService:
    """Get VectorService instance"""
    from app.services.vector_service import get_vector_service as get_vector_service_impl
    return get_vector_service_impl()


def get_patient_memory_repository() -> PatientMemoryRepository:
    """Get PatientMemoryRepository instance"""
    database = get_database()
    return PatientMemoryRepository(database.patient_memory)


def get_patient_context_service() -> PatientContextService:
    """Get PatientContextService instance"""
    database = get_database()
    
    from app.repositories.report_repository import ReportRepository
    from app.repositories.consultation_repository import ConsultationRepository
    from app.repositories.prescription_repository import PrescriptionRepository
    from app.repositories.reminder_repository import ReminderRepository
    from app.repositories.health_insight_repository import HealthInsightRepository
    from app.repositories.chat_session_repository import ChatSessionRepository
    
    return PatientContextService(
        user_repository=get_user_repository(),
        patient_memory_repository=get_patient_memory_repository(),
        report_repository=ReportRepository(database.reports),
        appointment_repository=get_appointment_repository(),
        consultation_repository=ConsultationRepository(database.consultations),
        prescription_repository=PrescriptionRepository(database.prescriptions),
        reminder_repository=ReminderRepository(database.reminders),
        health_insight_repository=HealthInsightRepository(database.health_insights),
        chat_session_repository=ChatSessionRepository(database.chat_sessions),
    )


def get_base_agent() -> BaseAgent:
    """Get BaseAgent instance (returns ConcreteBaseAgent placeholder)"""
    from typing import Any, Optional
    from app.agents.base.context import AgentContext

    class ConcreteBaseAgent(BaseAgent):
        async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
            return f"Response to: {input_data}"

    return ConcreteBaseAgent("Base Agent")


def get_intent_detection_service() -> IntentDetectionService:
    """Get IntentDetectionService instance"""
    from app.services.intent_detection_service import get_intent_detection_service as get_intent_detection_service_impl
    return get_intent_detection_service_impl()


def get_retrieval_agent() -> RetrievalAgent:
    """Get RetrievalAgent instance"""
    from app.agents.retrieval_agent import RetrievalAgent as ConcreteRetrievalAgent
    return ConcreteRetrievalAgent(
        intent_detector=get_intent_detection_service(),
        retrieval_service=get_retrieval_service(),
        context_assembly=get_context_assembly_service()
    )


_medical_knowledge_agent_instance = None
_symptom_agent_instance = None
_memory_agent_instance = None
_report_analysis_agent_instance = None
_drug_interaction_agent_instance = None
_doctor_recommendation_agent_instance = None
_reminder_agent_instance = None
_appointment_agent_instance = None


def get_report_repository() -> ReportRepository:
    """Get ReportRepository instance"""
    database = get_database()
    return ReportRepository(database.reports)


_ocr_service_instance = None
_pdf_extractor_instance = None
_image_preprocessor_instance = None
_document_parser_instance = None
_report_service_instance = None


def get_ocr_service():
    """Retrieve singleton OCRService instance"""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        from app.services.report_processing.ocr_service import OCRService
        _ocr_service_instance = OCRService()
    return _ocr_service_instance


def get_pdf_extractor():
    """Retrieve singleton PDFExtractor instance"""
    global _pdf_extractor_instance
    if _pdf_extractor_instance is None:
        from app.services.report_processing.pdf_extractor import PDFExtractor
        _pdf_extractor_instance = PDFExtractor()
    return _pdf_extractor_instance


def get_image_preprocessor():
    """Retrieve singleton ImagePreprocessor instance"""
    global _image_preprocessor_instance
    if _image_preprocessor_instance is None:
        from app.services.report_processing.image_preprocessor import ImagePreprocessor
        _image_preprocessor_instance = ImagePreprocessor()
    return _image_preprocessor_instance


def get_document_parser():
    """Retrieve singleton DocumentParser instance"""
    global _document_parser_instance
    if _document_parser_instance is None:
        from app.services.report_processing.document_parser import DocumentParser
        _document_parser_instance = DocumentParser(
            report_repository=get_report_repository(),
            pdf_extractor=get_pdf_extractor(),
            image_preprocessor=get_image_preprocessor(),
            ocr_service=get_ocr_service()
        )
    return _document_parser_instance


def get_report_service():
    """Retrieve singleton ReportService instance"""
    global _report_service_instance
    if _report_service_instance is None:
        from app.services.report_service import ReportService
        from app.repositories.user_repository import UserRepository
        database = get_database()
        _report_service_instance = ReportService(
            report_repository=get_report_repository(),
            user_repository=UserRepository(database.users)
        )
    return _report_service_instance


_document_classifier_instance = None
_medical_entity_extractor_instance = None
_laboratory_parser_instance = None
_medication_parser_instance = None
_medical_normalizer_instance = None
_extraction_validator_instance = None
_report_extraction_service_instance = None


def get_document_classifier():
    """Retrieve singleton DocumentClassifier instance"""
    global _document_classifier_instance
    if _document_classifier_instance is None:
        from app.services.report_extraction.document_classifier import DocumentClassifier
        _document_classifier_instance = DocumentClassifier(ai_service=get_ai_service())
    return _document_classifier_instance


def get_medical_entity_extractor():
    """Retrieve singleton MedicalEntityExtractor instance"""
    global _medical_entity_extractor_instance
    if _medical_entity_extractor_instance is None:
        from app.services.report_extraction.medical_entity_extractor import MedicalEntityExtractor
        _medical_entity_extractor_instance = MedicalEntityExtractor(ai_service=get_ai_service())
    return _medical_entity_extractor_instance


def get_laboratory_parser():
    """Retrieve singleton LaboratoryParser instance"""
    global _laboratory_parser_instance
    if _laboratory_parser_instance is None:
        from app.services.report_extraction.laboratory_parser import LaboratoryParser
        _laboratory_parser_instance = LaboratoryParser(ai_service=get_ai_service())
    return _laboratory_parser_instance


def get_medication_parser():
    """Retrieve singleton MedicationParser instance"""
    global _medication_parser_instance
    if _medication_parser_instance is None:
        from app.services.report_extraction.medication_parser import MedicationParser
        _medication_parser_instance = MedicationParser(ai_service=get_ai_service())
    return _medication_parser_instance


def get_medical_normalizer():
    """Retrieve singleton MedicalNormalizer instance"""
    global _medical_normalizer_instance
    if _medical_normalizer_instance is None:
        from app.services.report_extraction.normalizer import MedicalNormalizer
        _medical_normalizer_instance = MedicalNormalizer()
    return _medical_normalizer_instance


def get_extraction_validator():
    """Retrieve singleton ExtractionValidator instance"""
    global _extraction_validator_instance
    if _extraction_validator_instance is None:
        from app.services.report_extraction.validator import ExtractionValidator
        _extraction_validator_instance = ExtractionValidator()
    return _extraction_validator_instance


def get_report_extraction_service():
    """Retrieve singleton ReportExtractionService instance"""
    global _report_extraction_service_instance
    if _report_extraction_service_instance is None:
        from app.services.report_extraction.extractor import ReportExtractionService
        _report_extraction_service_instance = ReportExtractionService(
            report_repository=get_report_repository(),
            classifier=get_document_classifier(),
            entity_extractor=get_medical_entity_extractor(),
            lab_parser=get_laboratory_parser(),
            med_parser=get_medication_parser(),
            normalizer=get_medical_normalizer(),
            validator=get_extraction_validator()
        )
    return _report_extraction_service_instance


_laboratory_analyzer_instance = None
_clinical_rules_instance = None
_recommendation_engine_instance = None
_risk_engine_instance = None
_risk_analysis_service_instance = None


def get_laboratory_analyzer():
    """Retrieve singleton LaboratoryAnalyzer instance"""
    global _laboratory_analyzer_instance
    if _laboratory_analyzer_instance is None:
        from app.services.report_risk.laboratory_analyzer import LaboratoryAnalyzer
        _laboratory_analyzer_instance = LaboratoryAnalyzer()
    return _laboratory_analyzer_instance


def get_clinical_rules():
    """Retrieve singleton ClinicalRules instance"""
    global _clinical_rules_instance
    if _clinical_rules_instance is None:
        from app.services.report_risk.clinical_rules import ClinicalRules
        _clinical_rules_instance = ClinicalRules()
    return _clinical_rules_instance


def get_recommendation_engine():
    """Retrieve singleton RecommendationEngine instance"""
    global _recommendation_engine_instance
    if _recommendation_engine_instance is None:
        from app.services.report_risk.recommendation_engine import RecommendationEngine
        _recommendation_engine_instance = RecommendationEngine()
    return _recommendation_engine_instance


def get_risk_engine():
    """Retrieve singleton RiskEngine instance"""
    global _risk_engine_instance
    if _risk_engine_instance is None:
        from app.services.report_risk.risk_engine import RiskEngine
        _risk_engine_instance = RiskEngine(ai_service=get_ai_service())
    return _risk_engine_instance


def get_risk_analysis_service():
    """Retrieve singleton RiskAnalysisService instance"""
    global _risk_analysis_service_instance
    if _risk_analysis_service_instance is None:
        from app.services.report_risk.risk_analysis_service import RiskAnalysisService
        _risk_analysis_service_instance = RiskAnalysisService(
            report_repository=get_report_repository(),
            lab_analyzer=get_laboratory_analyzer(),
            clinical_rules=get_clinical_rules(),
            recommendation_engine=get_recommendation_engine(),
            risk_engine=get_risk_engine()
        )
    return _risk_analysis_service_instance


def get_report_analysis_agent() -> ReportAnalysisAgent:
    """Get singleton ReportAnalysisAgent instance"""
    global _report_analysis_agent_instance
    if _report_analysis_agent_instance is None:
        _report_analysis_agent_instance = ReportAnalysisAgent(
            retrieval_agent=get_retrieval_agent(),
            patient_context_service=get_patient_context_service(),
            report_repository=get_report_repository(),
            ai_service=get_ai_service()
        )
    return _report_analysis_agent_instance


def get_drug_interaction_agent() -> DrugInteractionAgent:
    """Get singleton DrugInteractionAgent instance"""
    global _drug_interaction_agent_instance
    if _drug_interaction_agent_instance is None:
        _drug_interaction_agent_instance = DrugInteractionAgent(
            retrieval_agent=get_retrieval_agent(),
            patient_memory_repository=get_patient_memory_repository(),
            ai_service=get_ai_service()
        )
    return _drug_interaction_agent_instance


def get_doctor_recommendation_agent() -> DoctorRecommendationAgent:
    """Get singleton DoctorRecommendationAgent instance"""
    global _doctor_recommendation_agent_instance
    if _doctor_recommendation_agent_instance is None:
        _doctor_recommendation_agent_instance = DoctorRecommendationAgent(
            retrieval_agent=get_retrieval_agent(),
            patient_context_service=get_patient_context_service(),
            doctor_availability_repository=get_doctor_availability_repository(),
            ai_service=get_ai_service()
        )
    return _doctor_recommendation_agent_instance


def get_medical_knowledge_agent() -> MedicalKnowledgeAgent:
    """Get singleton MedicalKnowledgeAgent instance"""
    global _medical_knowledge_agent_instance
    if _medical_knowledge_agent_instance is None:
        from app.agents.core.medical_knowledge_agent import MedicalKnowledgeAgent
        _medical_knowledge_agent_instance = MedicalKnowledgeAgent(
            retrieval_agent=get_retrieval_agent(),
            patient_context_service=get_patient_context_service(),
            ai_service=get_ai_service()
        )
    return _medical_knowledge_agent_instance


def get_symptom_agent() -> SymptomAgent:
    """Get singleton SymptomAgent instance"""
    global _symptom_agent_instance
    if _symptom_agent_instance is None:
        from app.agents.core.symptom_agent import SymptomAgent
        _symptom_agent_instance = SymptomAgent(
            retrieval_agent=get_retrieval_agent(),
            patient_context_service=get_patient_context_service(),
            ai_service=get_ai_service()
        )
    return _symptom_agent_instance


def get_memory_agent() -> MemoryAgent:
    """Get singleton MemoryAgent instance"""
    global _memory_agent_instance
    if _memory_agent_instance is None:
        from app.agents.core.memory_agent import MemoryAgent
        from app.repositories.chat_message_repository import ChatMessageRepository
        database = get_database()
        
        _memory_agent_instance = MemoryAgent(
            patient_memory_repository=get_patient_memory_repository(),
            chat_message_repository=ChatMessageRepository(database.chat_messages),
            retrieval_service=get_retrieval_service(),
            memory_sync_service=MemorySyncService(
                patient_memory_repository=get_patient_memory_repository(),
                user_repository=get_user_repository(),
                patient_summary_builder=get_patient_summary_builder(),
                embedding_service=get_embedding_service(),
                vector_service=get_vector_service(),
                index_version_service=get_index_version_service(),
                audit_log_service=get_audit_log_service()
            )
        )
    return _memory_agent_instance


def get_ai_orchestrator() -> AIOrchestrator:
    """Get AIOrchestrator instance"""
    from app.prompts.loader import PromptLoader
    
    return AIOrchestrator(
        groq_service=get_groq_service(),
        embedding_service=get_embedding_service(),
        vector_service=get_vector_service(),
        patient_context_service=get_patient_context_service(),
        prompt_loader=PromptLoader()
    )


_multi_agent_orchestrator_instance = None

def get_multi_agent_orchestrator():
    """Retrieve singleton instance of MultiAgentOrchestrator"""
    global _multi_agent_orchestrator_instance
    if _multi_agent_orchestrator_instance is None:
        from app.services.multi_agent_orchestrator import MultiAgentOrchestrator
        _multi_agent_orchestrator_instance = MultiAgentOrchestrator(
            engine=get_graph_engine()
        )
    return _multi_agent_orchestrator_instance


def get_index_version_service() -> IndexVersionService:
    """Get IndexVersionService instance"""
    from app.services.index_version_service import get_index_version_service as get_index_version_service_impl
    return get_index_version_service_impl()


def get_document_metadata_service() -> DocumentMetadataService:
    """Get DocumentMetadataService instance"""
    from app.services.document_metadata_service import get_document_metadata_service as get_document_metadata_service_impl
    return get_document_metadata_service_impl()


def get_document_indexing_service() -> DocumentIndexingService:
    """Get DocumentIndexingService instance"""
    from app.services.document_indexing_service import get_document_indexing_service as get_document_indexing_service_impl
    return get_document_indexing_service_impl()


def get_retrieval_service() -> RetrievalService:
    """Get RetrievalService instance"""
    from app.services.retrieval_service import get_retrieval_service as get_retrieval_service_impl
    return get_retrieval_service_impl()


def get_context_assembly_service() -> ContextAssemblyService:
    """Get ContextAssemblyService instance"""
    from app.services.context_assembly_service import get_context_assembly_service as get_context_assembly_service_impl
    return get_context_assembly_service_impl()


# ---------------------------------------------------------------------------
# Sync Pipeline & Event Dependencies
# ---------------------------------------------------------------------------

_event_dispatcher_instance = None
_event_queue_instance = None


def get_event_dispatcher() -> EventDispatcher:
    """Get EventDispatcher singleton instance"""
    global _event_dispatcher_instance
    if _event_dispatcher_instance is None:
        from app.events.dispatcher import EventDispatcher
        _event_dispatcher_instance = EventDispatcher()
    return _event_dispatcher_instance


def get_event_queue() -> EventQueue:
    """Get EventQueue background worker singleton instance"""
    global _event_queue_instance
    if _event_queue_instance is None:
        from app.events.queue import EventQueue
        _event_queue_instance = EventQueue()
    return _event_queue_instance


def get_patient_summary_builder() -> PatientSummaryBuilder:
    """Get PatientSummaryBuilder instance"""
    database = get_database()
    from app.repositories.report_repository import ReportRepository
    from app.repositories.consultation_repository import ConsultationRepository
    from app.repositories.prescription_repository import PrescriptionRepository
    from app.repositories.health_insight_repository import HealthInsightRepository
    
    return PatientSummaryBuilder(
        user_repository=get_user_repository(),
        report_repository=ReportRepository(database.reports),
        consultation_repository=ConsultationRepository(database.consultations),
        prescription_repository=PrescriptionRepository(database.prescriptions),
        health_insight_repository=HealthInsightRepository(database.health_insights),
        appointment_repository=get_appointment_repository()
    )


def get_memory_sync_service(
    patient_memory_repository: PatientMemoryRepository = Depends(get_patient_memory_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    patient_summary_builder: PatientSummaryBuilder = Depends(get_patient_summary_builder),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_service: VectorService = Depends(get_vector_service),
    index_version_service: IndexVersionService = Depends(get_index_version_service),
    audit_log_service = Depends(get_audit_log_service),
) -> MemorySyncService:
    """Get MemorySyncService instance"""
    return MemorySyncService(
        patient_memory_repository=patient_memory_repository,
        user_repository=user_repository,
        patient_summary_builder=patient_summary_builder,
        embedding_service=embedding_service,
        vector_service=vector_service,
        index_version_service=index_version_service,
        audit_log_service=audit_log_service
    )


def get_rag_cache_service():
    """Get RAGCacheService instance"""
    from app.services.rag_cache_service import get_rag_cache_service as get_rag_cache_service_impl
    return get_rag_cache_service_impl()


def get_rag_monitoring_service():
    """Get RAGMonitoringService instance"""
    from app.services.rag_monitoring_service import get_rag_monitoring_service as get_rag_monitoring_service_impl
    return get_rag_monitoring_service_impl()


def get_retrieval_evaluation_service():
    """Get RetrievalEvaluationService instance"""
    from app.services.retrieval_evaluation_service import get_retrieval_evaluation_service as get_retrieval_evaluation_service_impl
    return get_retrieval_evaluation_service_impl()


def get_rag_benchmark_service():
    """Get RAGBenchmarkService instance"""
    from app.services.rag_benchmark_service import get_rag_benchmark_service as get_rag_benchmark_service_impl
    return get_rag_benchmark_service_impl()


def get_graph_registry():
    """Get NodeRegistry singleton instance"""
    from app.graph.registry import get_graph_registry as get_registry_impl
    return get_registry_impl()


def get_graph_builder():
    """Get GraphBuilder singleton instance"""
    from app.graph.builder import get_graph_builder as get_builder_impl
    return get_builder_impl()


def get_graph_engine():
    """Get LangGraphEngine singleton instance"""
    from app.graph.engine import get_graph_engine as get_engine_impl
    return get_engine_impl()


_router_instance = None


def get_router_agent():
    """Retrieve singleton instance of RouterAgent"""
    global _router_instance
    if _router_instance is None:
        from app.agents.router import RouterAgent
        _router_instance = RouterAgent()
    return _router_instance


def get_reminder_repository():
    """Get ReminderRepository instance"""
    from app.repositories.reminder_repository import ReminderRepository
    database = get_database()
    return ReminderRepository(database.reminders)


def get_reminder_service() -> ReminderService:
    """Get ReminderService instance"""
    return ReminderService(
        reminder_repository=get_reminder_repository(),
        user_repository=get_user_repository()
    )


def get_reminder_agent() -> ReminderAgent:
    """Get singleton ReminderAgent instance"""
    global _reminder_agent_instance
    if _reminder_agent_instance is None:
        _reminder_agent_instance = ReminderAgent(
            reminder_service=get_reminder_service(),
            prompt_loader=PromptLoader()
        )
    return _reminder_agent_instance


def get_appointment_agent() -> AppointmentAgent:
    """Get singleton AppointmentAgent instance"""
    global _appointment_agent_instance
    if _appointment_agent_instance is None:
        _appointment_agent_instance = AppointmentAgent(
            appointment_service=get_appointment_service(),
            doctor_service=get_doctor_profile_service(),
            availability_service=get_doctor_availability_service(),
            prompt_loader=PromptLoader()
        )
    return _appointment_agent_instance








