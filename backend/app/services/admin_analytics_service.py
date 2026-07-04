"""
Nura - Admin Analytics Service
Business logic and database aggregations for administrative metrics and charts.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from app.repositories.user_repository import UserRepository
from app.repositories.doctor_repository import DoctorProfileRepository, DoctorAvailabilityRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.reminder_repository import ReminderRepository


class AdminAnalyticsService:
    """Service layer for platform operational analytics and reporting"""

    def __init__(
        self,
        user_repository: UserRepository,
        doctor_profile_repository: DoctorProfileRepository,
        doctor_availability_repository: DoctorAvailabilityRepository,
        appointment_repository: AppointmentRepository,
        payment_repository: PaymentRepository,
        consultation_repository: ConsultationRepository,
        report_repository: ReportRepository,
        prescription_repository: PrescriptionRepository,
        reminder_repository: ReminderRepository,
    ):
        self.user_repository = user_repository
        self.doctor_profile_repository = doctor_profile_repository
        self.doctor_availability_repository = doctor_availability_repository
        self.appointment_repository = appointment_repository
        self.payment_repository = payment_repository
        self.consultation_repository = consultation_repository
        self.report_repository = report_repository
        self.prescription_repository = prescription_repository
        self.reminder_repository = reminder_repository

    async def get_analytics(self) -> Dict[str, Any]:
        """Consolidate platform-wide administrative analytics data."""
        now = datetime.now(timezone.utc)
        today = now.date()

        # Date calculations (inclusive of today)
        start_7_days = datetime.combine(today - timedelta(days=6), datetime.min.time(), tzinfo=timezone.utc)
        start_30_days = datetime.combine(today - timedelta(days=29), datetime.min.time(), tzinfo=timezone.utc)

        # 1. User Metrics
        total_users = await self.user_repository.collection.count_documents({})
        active_users = await self.user_repository.collection.count_documents({"is_active": True})
        inactive_users = await self.user_repository.collection.count_documents({"is_active": False})
        patients_count = await self.user_repository.collection.count_documents({"role": "patient"})
        doctors_count = await self.user_repository.collection.count_documents({"role": "doctor"})
        admins_count = await self.user_repository.collection.count_documents({"role": "admin"})

        daily_users_7 = await self._get_daily_counts(self.user_repository.collection, start_7_days)
        daily_users_30 = await self._get_daily_counts(self.user_repository.collection, start_30_days)

        users_last_7_days = self._fill_missing_dates(daily_users_7, start_7_days, 7)
        users_last_30_days = self._fill_missing_dates(daily_users_30, start_30_days, 30)

        # 2. Doctor Metrics
        total_doctors = await self.doctor_profile_repository.collection.count_documents({})
        verified_doctors = await self.doctor_profile_repository.collection.count_documents({"profile_status": "verified"})
        pending_doctors = await self.doctor_profile_repository.collection.count_documents({"profile_status": "pending"})
        rejected_doctors = await self.doctor_profile_repository.collection.count_documents({"profile_status": "rejected"})
        suspended_doctors = await self.doctor_profile_repository.collection.count_documents({"profile_status": "suspended"})

        # Unique count of doctors with availability
        pipeline_avail = [
            {"$group": {"_id": "$doctor_id"}},
            {"$count": "count"}
        ]
        cursor_avail = self.doctor_availability_repository.collection.aggregate(pipeline_avail)
        res_avail = await cursor_avail.to_list(length=1)
        doctors_with_availability = res_avail[0]["count"] if res_avail else 0

        # Verified doctor profiles linked to active user accounts
        active_doctors = await self.user_repository.collection.count_documents({"role": "doctor", "is_active": True})

        # 3. Appointment Metrics
        total_appointments = await self.appointment_repository.collection.count_documents({})
        pending_appointments = await self.appointment_repository.collection.count_documents({"status": "pending"})
        approved_appointments = await self.appointment_repository.collection.count_documents({"status": "approved"})
        completed_appointments = await self.appointment_repository.collection.count_documents({"status": "completed"})
        cancelled_appointments = await self.appointment_repository.collection.count_documents({"status": "cancelled"})
        rejected_appointments = await self.appointment_repository.collection.count_documents({"status": "rejected"})

        daily_appts_7 = await self._get_daily_counts(self.appointment_repository.collection, start_7_days)
        daily_appts_30 = await self._get_daily_counts(self.appointment_repository.collection, start_30_days)

        appointments_last_7_days = self._fill_missing_dates(daily_appts_7, start_7_days, 7)
        appointments_last_30_days = self._fill_missing_dates(daily_appts_30, start_30_days, 30)

        # 4. Revenue Metrics (payments with completed, approved, or held status)
        payment_filter = {"payment_status": {"$in": ["success", "paid", "completed", "approved", "held"]}}
        pipeline_rev = [
            {"$match": payment_filter},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$amount"},
                "doctor": {"$sum": "$doctor_amount"},
                "platform": {"$sum": "$platform_fee"}
            }}
        ]
        cursor_rev = self.payment_repository.collection.aggregate(pipeline_rev)
        res_rev = await cursor_rev.to_list(length=1)

        total_revenue = float(res_rev[0]["total"]) if res_rev else 0.0
        doctor_earnings = float(res_rev[0]["doctor"]) if res_rev else 0.0
        platform_revenue = float(res_rev[0]["platform"]) if res_rev else 0.0

        daily_rev_7 = await self._get_daily_revenue(self.payment_repository.collection, start_7_days)
        daily_rev_30 = await self._get_daily_revenue(self.payment_repository.collection, start_30_days)

        revenue_last_7_days = self._fill_missing_dates(daily_rev_7, start_7_days, 7, value_key="amount", default_val=0.0)
        revenue_last_30_days = self._fill_missing_dates(daily_rev_30, start_30_days, 30, value_key="amount", default_val=0.0)

        # 5. Healthcare Activity Metrics
        reports_uploaded = await self.report_repository.collection.count_documents({})
        consultations_completed = await self.consultation_repository.collection.count_documents({})
        prescriptions_created = await self.prescription_repository.collection.count_documents({})
        reminders_created = await self.reminder_repository.collection.count_documents({"active": True})

        daily_reports_30 = await self._get_daily_counts(self.report_repository.collection, start_30_days)
        daily_consults_30 = await self._get_daily_counts(self.consultation_repository.collection, start_30_days)

        reports_last_30_days = self._fill_missing_dates(daily_reports_30, start_30_days, 30)
        consultations_last_30_days = self._fill_missing_dates(daily_consults_30, start_30_days, 30)

        return {
            "users": {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "patients_count": patients_count,
                "doctors_count": doctors_count,
                "admins_count": admins_count,
                "users_last_7_days": users_last_7_days,
                "users_last_30_days": users_last_30_days,
            },
            "doctors": {
                "total_doctors": total_doctors,
                "verified_doctors": verified_doctors,
                "pending_doctors": pending_doctors,
                "rejected_doctors": rejected_doctors,
                "suspended_doctors": suspended_doctors,
                "doctors_with_availability": doctors_with_availability,
                "active_doctors": active_doctors,
            },
            "appointments": {
                "total_appointments": total_appointments,
                "pending_appointments": pending_appointments,
                "approved_appointments": approved_appointments,
                "completed_appointments": completed_appointments,
                "cancelled_appointments": cancelled_appointments,
                "rejected_appointments": rejected_appointments,
                "appointments_last_7_days": appointments_last_7_days,
                "appointments_last_30_days": appointments_last_30_days,
            },
            "revenue": {
                "total_revenue": total_revenue,
                "doctor_earnings": doctor_earnings,
                "platform_revenue": platform_revenue,
                "revenue_last_7_days": revenue_last_7_days,
                "revenue_last_30_days": revenue_last_30_days,
            },
            "healthcare": {
                "reports_uploaded": reports_uploaded,
                "consultations_completed": consultations_completed,
                "prescriptions_created": prescriptions_created,
                "reminders_created": reminders_created,
                "reports_last_30_days": reports_last_30_days,
                "consultations_last_30_days": consultations_last_30_days,
            }
        }

    async def _get_daily_counts(
        self,
        collection,
        start_date: datetime,
        date_field: str = "created_at"
    ) -> Dict[str, int]:
        pipeline = [
            {"$match": {date_field: {"$gte": start_date}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": f"${date_field}"}},
                "count": {"$sum": 1}
            }}
        ]
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=1000)
        return {r["_id"]: r["count"] for r in results}

    async def _get_daily_revenue(
        self,
        collection,
        start_date: datetime,
        date_field: str = "created_at"
    ) -> Dict[str, float]:
        payment_filter = {"payment_status": {"$in": ["success", "paid", "completed", "approved", "held"]}}
        pipeline = [
            {"$match": {
                date_field: {"$gte": start_date},
                **payment_filter
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": f"${date_field}"}},
                "total": {"$sum": "$amount"}
            }}
        ]
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=1000)
        return {r["_id"]: float(r["total"]) for r in results}

    def _fill_missing_dates(
        self,
        daily_data: Dict[str, Any],
        start_date: datetime,
        num_days: int,
        value_key: str = "count",
        default_val: Any = 0
    ) -> List[Dict[str, Any]]:
        output = []
        for i in range(num_days):
            d = start_date + timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            output.append({
                "date": date_str,
                value_key: daily_data.get(date_str, default_val)
            })
        return output
