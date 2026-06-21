"""
Nura - Patient Dashboard Service
Aggregates patient-specific data for the dashboard API endpoint
"""

from datetime import datetime, timezone, date
from typing import List

from app.schemas.dashboard import PatientDashboardResponse, RecentHealthInsight
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.health_insight_repository import HealthInsightRepository


def _today_iso() -> str:
    """Return today's date as YYYY-MM-DD string."""
    return date.today().isoformat()


class PatientDashboardService:
    """Aggregation service for the patient dashboard"""

    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        reminder_repository: ReminderRepository,
        report_repository: ReportRepository,
        notification_repository: NotificationRepository,
        health_insight_repository: HealthInsightRepository,
    ):
        self.appointment_repository = appointment_repository
        self.reminder_repository = reminder_repository
        self.report_repository = report_repository
        self.notification_repository = notification_repository
        self.health_insight_repository = health_insight_repository

    async def get_dashboard(self, patient_id: str) -> PatientDashboardResponse:
        """Aggregate all patient dashboard data for the given patient_id."""

        today = _today_iso()

        # 1. Upcoming appointments (pending or approved, slot_date >= today)
        upcoming_appointments_count = await self.appointment_repository.collection.count_documents({
            "patient_id": patient_id,
            "status": {"$in": ["pending", "approved"]},
            "slot_date": {"$gte": today},
        })

        # 2. Active reminders
        active_reminders_count = await self.reminder_repository.collection.count_documents({
            "patient_id": patient_id,
            "status": "active",
        })

        # 3. Total reports
        reports_count = await self.report_repository.collection.count_documents({
            "patient_id": patient_id,
        })

        # 4. Unread notifications (uses user_id and read=False per notification model)
        unread_notifications_count = await self.notification_repository.collection.count_documents({
            "user_id": patient_id,
            "read": False,
        })

        # 5. Recent health insights (last 5, newest first)
        cursor = (
            self.health_insight_repository.collection
            .find({"patient_id": patient_id})
            .sort("created_at", -1)
            .limit(5)
        )
        recent_docs = await cursor.to_list(length=5)
        recent_health_insights: List[RecentHealthInsight] = []
        for doc in recent_docs:
            recent_health_insights.append(
                RecentHealthInsight(
                    id=str(doc["_id"]),
                    title=doc.get("title", ""),
                    severity=doc.get("severity"),
                    created_at=doc.get("created_at", datetime.now(timezone.utc)),
                )
            )

        return PatientDashboardResponse(
            upcoming_appointments_count=upcoming_appointments_count,
            active_reminders_count=active_reminders_count,
            reports_count=reports_count,
            unread_notifications_count=unread_notifications_count,
            recent_health_insights=recent_health_insights,
        )
