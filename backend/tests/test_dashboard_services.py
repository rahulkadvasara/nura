"""
Nura - Dashboard Services Tests
Unit tests for PatientDashboardService, DoctorDashboardService, and AdminDashboardService
using mocked MongoDB collections
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers: mock collection factories
# ---------------------------------------------------------------------------

def make_count_collection(**count_map):
    """Create a mock collection that returns different counts based on filter signature."""
    col = MagicMock()

    async def count_documents(filter_dict, **kwargs):
        # Return the first match in count_map by checking keys present in filter_dict
        for key, count in count_map.items():
            if key in filter_dict or key == "_default":
                return count
        return 0

    col.count_documents = count_documents
    return col


# ---------------------------------------------------------------------------
# PatientDashboardService
# ---------------------------------------------------------------------------

class TestPatientDashboardService:

    @pytest.mark.asyncio
    async def test_patient_dashboard_all_counts(self):
        """Patient dashboard aggregates all counters correctly"""
        from app.services.patient_dashboard_service import PatientDashboardService
        from app.repositories.appointment_repository import AppointmentRepository
        from app.repositories.reminder_repository import ReminderRepository
        from app.repositories.report_repository import ReportRepository
        from app.repositories.notification_repository import NotificationRepository
        from app.repositories.health_insight_repository import HealthInsightRepository

        patient_id = "patient_001"

        # Mock collections
        appt_col = MagicMock()
        appt_col.count_documents = AsyncMock(return_value=3)

        reminder_col = MagicMock()
        reminder_col.count_documents = AsyncMock(return_value=5)

        report_col = MagicMock()
        report_col.count_documents = AsyncMock(return_value=7)

        notif_col = MagicMock()
        notif_col.count_documents = AsyncMock(return_value=2)

        # Health insights cursor mock
        insight_docs = [
            {
                "_id": "ins001",
                "title": "High Cholesterol",
                "severity": "high",
                "created_at": utc_now(),
                "patient_id": patient_id,
            }
        ]
        cursor_mock = AsyncMock()
        cursor_mock.to_list = AsyncMock(return_value=insight_docs)

        insight_col = MagicMock()
        insight_col.find = MagicMock(return_value=MagicMock(
            sort=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=cursor_mock)
            ))
        ))

        appt_repo = AppointmentRepository(appt_col)
        reminder_repo = ReminderRepository(reminder_col)
        report_repo = ReportRepository(report_col)
        notif_repo = NotificationRepository(notif_col)
        insight_repo = HealthInsightRepository(insight_col)

        service = PatientDashboardService(
            appointment_repository=appt_repo,
            reminder_repository=reminder_repo,
            report_repository=report_repo,
            notification_repository=notif_repo,
            health_insight_repository=insight_repo,
        )

        result = await service.get_dashboard(patient_id)

        assert result.upcoming_appointments_count == 3
        assert result.active_reminders_count == 5
        assert result.reports_count == 7
        assert result.unread_notifications_count == 2
        assert len(result.recent_health_insights) == 1
        assert result.recent_health_insights[0].title == "High Cholesterol"
        assert result.recent_health_insights[0].severity == "high"

    @pytest.mark.asyncio
    async def test_patient_dashboard_empty_data(self):
        """Patient dashboard handles zero counts and no insights gracefully"""
        from app.services.patient_dashboard_service import PatientDashboardService
        from app.repositories.appointment_repository import AppointmentRepository
        from app.repositories.reminder_repository import ReminderRepository
        from app.repositories.report_repository import ReportRepository
        from app.repositories.notification_repository import NotificationRepository
        from app.repositories.health_insight_repository import HealthInsightRepository

        patient_id = "patient_empty"

        col_zero = MagicMock()
        col_zero.count_documents = AsyncMock(return_value=0)

        cursor_mock = AsyncMock()
        cursor_mock.to_list = AsyncMock(return_value=[])

        insight_col = MagicMock()
        insight_col.find = MagicMock(return_value=MagicMock(
            sort=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=cursor_mock)
            ))
        ))

        service = PatientDashboardService(
            appointment_repository=AppointmentRepository(col_zero),
            reminder_repository=ReminderRepository(col_zero),
            report_repository=ReportRepository(col_zero),
            notification_repository=NotificationRepository(col_zero),
            health_insight_repository=HealthInsightRepository(insight_col),
        )

        result = await service.get_dashboard(patient_id)

        assert result.upcoming_appointments_count == 0
        assert result.active_reminders_count == 0
        assert result.reports_count == 0
        assert result.unread_notifications_count == 0
        assert result.recent_health_insights == []


# ---------------------------------------------------------------------------
# DoctorDashboardService
# ---------------------------------------------------------------------------

class TestDoctorDashboardService:

    @pytest.mark.asyncio
    async def test_doctor_dashboard_all_counts(self):
        """Doctor dashboard aggregates all counters and wallet data correctly"""
        from app.services.doctor_dashboard_service import DoctorDashboardService
        from app.repositories.appointment_repository import AppointmentRepository
        from app.repositories.doctor_wallet_repository import DoctorWalletRepository

        doctor_id = "doctor_001"

        appt_col = MagicMock()
        appt_col.count_documents = AsyncMock(side_effect=[4, 6, 2])  # today, upcoming, pending
        appt_col.distinct = AsyncMock(return_value=["p1", "p2", "p3"])

        wallet_doc = {
            "_id": "w001",
            "doctor_id": doctor_id,
            "available_balance": 12500.0,
            "total_earned": 45000.0,
        }
        wallet_col = MagicMock()
        wallet_col.find_one = AsyncMock(return_value=wallet_doc)

        profile_repo = AsyncMock()
        profile_repo.get_by_user_id.return_value = None
        doc_repo = AsyncMock()

        service = DoctorDashboardService(
            appointment_repository=AppointmentRepository(appt_col),
            doctor_wallet_repository=DoctorWalletRepository(wallet_col),
            doctor_profile_repository=profile_repo,
            doctor_document_repository=doc_repo,
        )

        result = await service.get_dashboard(doctor_id)

        assert result.todays_appointments_count == 4
        assert result.upcoming_appointments_count == 6
        assert result.total_patients_count == 3
        assert result.pending_approvals_count == 2
        assert result.wallet_balance == 12500.0
        assert result.total_earnings == 45000.0

    @pytest.mark.asyncio
    async def test_doctor_dashboard_no_wallet(self):
        """Doctor dashboard returns zero wallet values when no wallet exists"""
        from app.services.doctor_dashboard_service import DoctorDashboardService
        from app.repositories.appointment_repository import AppointmentRepository
        from app.repositories.doctor_wallet_repository import DoctorWalletRepository

        doctor_id = "doctor_no_wallet"

        appt_col = MagicMock()
        appt_col.count_documents = AsyncMock(return_value=0)
        appt_col.distinct = AsyncMock(return_value=[])

        wallet_col = MagicMock()
        wallet_col.find_one = AsyncMock(return_value=None)

        profile_repo = AsyncMock()
        profile_repo.get_by_user_id.return_value = None
        doc_repo = AsyncMock()

        service = DoctorDashboardService(
            appointment_repository=AppointmentRepository(appt_col),
            doctor_wallet_repository=DoctorWalletRepository(wallet_col),
            doctor_profile_repository=profile_repo,
            doctor_document_repository=doc_repo,
        )

        result = await service.get_dashboard(doctor_id)

        assert result.wallet_balance == 0.0
        assert result.total_earnings == 0.0
        assert result.total_patients_count == 0

    @pytest.mark.asyncio
    async def test_doctor_dashboard_no_appointments(self):
        """Doctor dashboard returns all zeros when no appointments exist"""
        from app.services.doctor_dashboard_service import DoctorDashboardService
        from app.repositories.appointment_repository import AppointmentRepository
        from app.repositories.doctor_wallet_repository import DoctorWalletRepository

        doctor_id = "doctor_new"

        appt_col = MagicMock()
        appt_col.count_documents = AsyncMock(return_value=0)
        appt_col.distinct = AsyncMock(return_value=[])

        wallet_col = MagicMock()
        wallet_col.find_one = AsyncMock(return_value=None)

        from app.repositories.doctor_repository import DoctorProfileRepository, DoctorDocumentRepository
        
        profile_repo = AsyncMock()
        profile_repo.get_by_user_id.return_value = None
        doc_repo = AsyncMock()
        
        service = DoctorDashboardService(
            appointment_repository=AppointmentRepository(appt_col),
            doctor_wallet_repository=DoctorWalletRepository(wallet_col),
            doctor_profile_repository=profile_repo,
            doctor_document_repository=doc_repo,
        )

        result = await service.get_dashboard(doctor_id)

        assert result.todays_appointments_count == 0
        assert result.upcoming_appointments_count == 0
        assert result.pending_approvals_count == 0


# ---------------------------------------------------------------------------
# AdminDashboardService
# ---------------------------------------------------------------------------

class TestAdminDashboardService:

    @pytest.mark.asyncio
    async def test_admin_dashboard_all_counts(self):
        """Admin dashboard aggregates all platform-wide metrics correctly"""
        from app.services.admin_dashboard_service import AdminDashboardService
        from app.repositories.user_repository import UserRepository
        from app.repositories.appointment_repository import AppointmentRepository
        from app.repositories.consultation_repository import ConsultationRepository
        from app.repositories.payment_repository import PaymentRepository
        from app.repositories.doctor_repository import DoctorProfileRepository

        # User counts: total=100, patients=80, doctors=20
        user_col = MagicMock()
        user_col.count_documents = AsyncMock(side_effect=[100, 80, 20])

        # Doctor profiles: pending=5
        doctor_col = MagicMock()
        doctor_col.count_documents = AsyncMock(return_value=5)

        # Appointments: total=200
        appt_col = MagicMock()
        appt_col.count_documents = AsyncMock(return_value=200)

        # Payments: revenue aggregation
        revenue_result = [{"_id": None, "total": 99750.0}]
        cursor_mock = AsyncMock()
        cursor_mock.to_list = AsyncMock(return_value=revenue_result)
        payment_col = MagicMock()
        payment_col.aggregate = MagicMock(return_value=cursor_mock)

        # Consultations: active=50
        consult_col = MagicMock()
        consult_col.count_documents = AsyncMock(return_value=50)

        # Mock other collections with zero counts
        col_zero = MagicMock()
        col_zero.count_documents = AsyncMock(return_value=0)

        from app.repositories.report_repository import ReportRepository
        from app.repositories.reminder_repository import ReminderRepository
        from app.repositories.chat_session_repository import ChatSessionRepository
        service = AdminDashboardService(
            user_repository=UserRepository(user_col),
            appointment_repository=AppointmentRepository(appt_col),
            consultation_repository=ConsultationRepository(consult_col),
            payment_repository=PaymentRepository(payment_col),
            doctor_profile_repository=DoctorProfileRepository(doctor_col),
            report_repository=ReportRepository(col_zero),
            reminder_repository=ReminderRepository(col_zero),
            chat_session_repository=ChatSessionRepository(col_zero),
        )

        result = await service.get_dashboard()

        assert result.total_users_count == 100
        assert result.total_patients_count == 80
        assert result.total_doctors_count == 20
        assert result.pending_doctor_verifications_count == 5
        assert result.total_appointments_count == 200
        assert result.total_revenue == 99750.0
        assert result.active_consultations_count == 50

    @pytest.mark.asyncio
    async def test_admin_dashboard_zero_revenue(self):
        """Admin dashboard returns 0.0 revenue when no payments exist"""
        from app.services.admin_dashboard_service import AdminDashboardService
        from app.repositories.user_repository import UserRepository
        from app.repositories.appointment_repository import AppointmentRepository
        from app.repositories.consultation_repository import ConsultationRepository
        from app.repositories.payment_repository import PaymentRepository
        from app.repositories.doctor_repository import DoctorProfileRepository

        col_zero = MagicMock()
        col_zero.count_documents = AsyncMock(return_value=0)

        cursor_empty = AsyncMock()
        cursor_empty.to_list = AsyncMock(return_value=[])
        payment_col = MagicMock()
        payment_col.aggregate = MagicMock(return_value=cursor_empty)
        payment_col.count_documents = AsyncMock(return_value=0)

        from app.repositories.report_repository import ReportRepository
        from app.repositories.reminder_repository import ReminderRepository
        from app.repositories.chat_session_repository import ChatSessionRepository
        service = AdminDashboardService(
            user_repository=UserRepository(col_zero),
            appointment_repository=AppointmentRepository(col_zero),
            consultation_repository=ConsultationRepository(col_zero),
            payment_repository=PaymentRepository(payment_col),
            doctor_profile_repository=DoctorProfileRepository(col_zero),
            report_repository=ReportRepository(col_zero),
            reminder_repository=ReminderRepository(col_zero),
            chat_session_repository=ChatSessionRepository(col_zero),
        )

        result = await service.get_dashboard()

        assert result.total_revenue == 0.0
        assert result.total_users_count == 0
