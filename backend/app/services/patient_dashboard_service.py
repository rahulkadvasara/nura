"""
Nura - Patient Dashboard Service
Aggregates patient-specific data for the dashboard API endpoint
"""

from datetime import datetime, timezone, date
from typing import List

from app.schemas.dashboard import (
    PatientDashboardResponse,
    RecentHealthInsight,
    PatientDashboardConsultation,
    PatientDashboardPrescription,
)
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.health_insight_repository import HealthInsightRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.doctor_repository import DoctorProfileRepository
from app.repositories.user_repository import UserRepository


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
        consultation_repository: ConsultationRepository,
        prescription_repository: PrescriptionRepository,
        doctor_profile_repository: DoctorProfileRepository,
        user_repository: UserRepository,
    ):
        self.appointment_repository = appointment_repository
        self.reminder_repository = reminder_repository
        self.report_repository = report_repository
        self.notification_repository = notification_repository
        self.health_insight_repository = health_insight_repository
        self.consultation_repository = consultation_repository
        self.prescription_repository = prescription_repository
        self.doctor_profile_repository = doctor_profile_repository
        self.user_repository = user_repository

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

        # 6. Recent Consultation
        consultation_doc = await self.consultation_repository.collection.find_one(
            {"patient_id": patient_id},
            sort=[("created_at", -1)]
        )
        recent_consultation = None
        if consultation_doc:
            from app.models.appointment import ConsultationInDB
            consultation = ConsultationInDB.from_mongo(consultation_doc)
            
            # Resolve doctor details
            doctor_profile = await self.doctor_profile_repository.get(consultation.doctor_id)
            doctor_name = "Unknown Doctor"
            specialization = "General Medicine"
            if doctor_profile:
                specialization = doctor_profile.specialization
                doctor_user = await self.user_repository.get(doctor_profile.user_id)
                if doctor_user:
                    doctor_name = doctor_user.full_name
            
            # Resolve date using appointment slot
            appointment = await self.appointment_repository.get(consultation.appointment_id)
            date_val = consultation.created_at
            if appointment:
                try:
                    date_val = datetime.strptime(f"{appointment.slot_date} {appointment.slot_time}", "%Y-%m-%d %H:%M")
                    date_val = date_val.replace(tzinfo=timezone.utc)
                except Exception:
                    pass
            
            recent_consultation = PatientDashboardConsultation(
                id=consultation.id,
                doctor_name=doctor_name,
                specialization=specialization,
                date=date_val,
                diagnosis=consultation.diagnosis,
            )

        # 7. Recent Prescription
        prescription_doc = await self.prescription_repository.collection.find_one(
            {"patient_id": patient_id},
            sort=[("created_at", -1)]
        )
        recent_prescription = None
        if prescription_doc:
            from app.models.appointment import PrescriptionInDB
            prescription = PrescriptionInDB.from_mongo(prescription_doc)
            
            # Resolve doctor name
            doctor_profile = await self.doctor_profile_repository.get(prescription.doctor_id)
            doctor_name = "Unknown Doctor"
            if doctor_profile:
                doctor_user = await self.user_repository.get(doctor_profile.user_id)
                if doctor_user:
                    doctor_name = doctor_user.full_name
                    
            recent_prescription = PatientDashboardPrescription(
                id=prescription.id,
                doctor_name=doctor_name,
                date=prescription.created_at,
                medications_count=len(prescription.medications),
            )

        return PatientDashboardResponse(
            upcoming_appointments_count=upcoming_appointments_count,
            active_reminders_count=active_reminders_count,
            reports_count=reports_count,
            unread_notifications_count=unread_notifications_count,
            recent_health_insights=recent_health_insights,
            recent_consultation=recent_consultation,
            recent_prescription=recent_prescription,
        )
