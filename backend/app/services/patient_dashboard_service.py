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


def format_summary_to_bullets(text: str, max_bullets: int = 6) -> str:
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    
    # Remove double periods
    while ".." in text:
        text = text.replace("..", ".")

    import re
    parts = []
    for chunk in text.split(';'):
        chunk = chunk.strip()
        if not chunk:
            continue
        sentences = re.split(r'(?<=\.)\s+(?=[A-Z])', chunk)
        for s in sentences:
            s = s.strip()
            if s:
                parts.append(s)

    formatted_lines = []
    for p in parts[:max_bullets]:
        if not p.endswith('.') and not p.endswith(':'):
            p += '.'
        formatted_lines.append(f"• {p}")

    return "\n".join(formatted_lines)


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

        # 5. Health insights (Longitudinal Health Summary from patient_memory FIRST)
        recent_health_insights: List[RecentHealthInsight] = []
        try:
            db = self.health_insight_repository.collection.database
            memory_doc = await db["patient_memory"].find_one({"patient_id": patient_id})
            if memory_doc:
                mem_summary = memory_doc.get("longitudinal_summary") or memory_doc.get("ai_summary")
                if mem_summary and isinstance(mem_summary, str) and mem_summary.strip():
                    recent_health_insights.append(
                        RecentHealthInsight(
                            id=str(memory_doc.get("_id", "patient_memory")),
                            title="Longitudinal Health Summary",
                            summary=format_summary_to_bullets(mem_summary, max_bullets=8),
                            severity=memory_doc.get("overall_risk") if memory_doc.get("overall_risk") in ["low", "medium", "high"] else None,
                            created_at=memory_doc.get("updated_at") or memory_doc.get("last_updated") or datetime.now(timezone.utc),
                        )
                    )
        except Exception as err:
            pass

        # Fallback: If patient_memory is empty, surface recent report summaries
        if not recent_health_insights:
            report_cursor = (
                self.report_repository.collection
                .find({"patient_id": patient_id})
                .sort("created_at", -1)
                .limit(3)
            )
            report_docs = await report_cursor.to_list(length=3)
            for rdoc in report_docs:
                rep_summary = rdoc.get("summary") or rdoc.get("patient_summary") or rdoc.get("ai_summary")
                if isinstance(rep_summary, dict):
                    rep_summary = rep_summary.get("patient_summary") or rep_summary.get("ai_summary") or rep_summary.get("summary") or ""
                
                filename = rdoc.get("filename") or "Medical Report"
                risk = rdoc.get("overall_risk") or rdoc.get("risk_level")
                if rep_summary and isinstance(rep_summary, str) and rep_summary.strip():
                    recent_health_insights.append(
                        RecentHealthInsight(
                            id=str(rdoc["_id"]),
                            title=f"{filename}",
                            summary=format_summary_to_bullets(rep_summary, max_bullets=3),
                            severity=risk if risk in ["low", "medium", "high"] else None,
                            created_at=rdoc.get("created_at", datetime.now(timezone.utc)),
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
