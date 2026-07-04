"""
Nura - Admin Dashboard Service
Aggregates platform-wide data for the admin dashboard API endpoint
"""

from app.schemas.dashboard import AdminDashboardResponse
from app.repositories.user_repository import UserRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.doctor_repository import DoctorProfileRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.chat_session_repository import ChatSessionRepository


class AdminDashboardService:
    """Aggregation service for the admin dashboard"""

    def __init__(
        self,
        user_repository: UserRepository,
        appointment_repository: AppointmentRepository,
        consultation_repository: ConsultationRepository,
        payment_repository: PaymentRepository,
        doctor_profile_repository: DoctorProfileRepository,
        report_repository: ReportRepository,
        reminder_repository: ReminderRepository,
        chat_session_repository: ChatSessionRepository,
    ):
        self.user_repository = user_repository
        self.appointment_repository = appointment_repository
        self.consultation_repository = consultation_repository
        self.payment_repository = payment_repository
        self.doctor_profile_repository = doctor_profile_repository
        self.report_repository = report_repository
        self.reminder_repository = reminder_repository
        self.chat_session_repository = chat_session_repository

    async def get_dashboard(self) -> AdminDashboardResponse:
        """Aggregate platform-wide admin dashboard data."""

        # 1. Total users
        total_users_count = await self.user_repository.collection.count_documents({})

        # 2. Total patients
        total_patients_count = await self.user_repository.collection.count_documents(
            {"role": "patient"}
        )

        # 3. Total doctors
        total_doctors_count = await self.user_repository.collection.count_documents(
            {"role": "doctor"}
        )

        # 4. Pending doctor verifications (profiles with profile_status=pending)
        pending_doctor_verifications_count = await self.doctor_profile_repository.collection.count_documents(
            {"profile_status": "pending"}
        )

        # 5. Total appointments
        total_appointments_count = await self.appointment_repository.collection.count_documents({})

        # 6. Total revenue (sum of successful payment amounts using aggregation pipeline)
        success_query = {"payment_status": {"$in": ["success", "paid", "completed", "approved", "held"]}}
        pipeline = [
            {"$match": success_query},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        cursor = self.payment_repository.collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        total_revenue = float(results[0]["total"]) if results else 0.0
 
        # 7. Active consultations (total consultation records)
        active_consultations_count = await self.consultation_repository.collection.count_documents({})
 
        # 8. Platform earnings (sum of platform fee splits for successful payments)
        pipeline_earnings = [
            {"$match": success_query},
            {"$group": {"_id": None, "total": {"$sum": "$platform_fee"}}}
        ]
        cursor_earnings = self.payment_repository.collection.aggregate(pipeline_earnings)
        results_earnings = await cursor_earnings.to_list(length=1)
        platform_earnings = float(results_earnings[0]["total"]) if results_earnings else 0.0


        # 9. Reports count
        reports_count = await self.report_repository.collection.count_documents({})

        # 10. Reminders count (active reminders)
        reminders_count = await self.reminder_repository.collection.count_documents({"active": True})

        # 11. Active chat sessions
        active_chats_count = await self.chat_session_repository.collection.count_documents({"active": True})

        # 12. Verified doctor profile count
        verified_doctors_count = await self.doctor_profile_repository.collection.count_documents({"profile_status": "verified"})

        return AdminDashboardResponse(
            total_users_count=total_users_count,
            total_patients_count=total_patients_count,
            total_doctors_count=total_doctors_count,
            pending_doctor_verifications_count=pending_doctor_verifications_count,
            total_appointments_count=total_appointments_count,
            total_revenue=total_revenue,
            platform_earnings=platform_earnings,
            active_consultations_count=active_consultations_count,
            reports_count=reports_count,
            reminders_count=reminders_count,
            active_chats_count=active_chats_count,
            verified_doctors_count=verified_doctors_count,
        )

