"""
Nura - Healthcare Context Resolver
Detects context triggers from user messages and resolves structured healthcare objects
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.report_service import ReportService
from app.services.reminder_service import ReminderService
from app.services.appointment_service import AppointmentService
from app.services.prescription_service import PrescriptionService
from app.services.doctor_service import DoctorProfileService

logger = logging.getLogger(__name__)


SPECIALTY_MAP = {
    "back pain": "Orthopedic",
    "back": "Orthopedic",
    "spine": "Orthopedic",
    "joint": "Orthopedic",
    "bone": "Orthopedic",
    "knee": "Orthopedic",
    "shoulder": "Orthopedic",
    "chest pain": "Cardiology",
    "heart": "Cardiology",
    "cardio": "Cardiology",
    "blood pressure": "Cardiology",
    "headache": "Neurology",
    "migraine": "Neurology",
    "dizzy": "Neurology",
    "brain": "Neurology",
    "skin": "Dermatology",
    "rash": "Dermatology",
    "acne": "Dermatology",
    "eczema": "Dermatology",
    "stomach": "Gastroenterology",
    "acid": "Gastroenterology",
    "gut": "Gastroenterology",
    "child": "Pediatrics",
    "kid": "Pediatrics",
    "baby": "Pediatrics",
    "eye": "Ophthalmology",
    "ear": "ENT",
    "throat": "ENT",
}


def detect_specialty_from_query(query: str) -> Optional[str]:
    q_lower = query.lower()
    for symptom, specialty in SPECIALTY_MAP.items():
        if symptom in q_lower:
            return specialty
    for specialty in ["cardiologist", "cardiology", "dermatologist", "dermatology", "neurologist", "neurology", "pediatrician", "pediatrics", "orthopedic", "orthopedics", "gastroenterologist", "ophthalmologist", "ent"]:
        if specialty in q_lower:
            return specialty.capitalize()
    return None


class HealthcareContextResolver:
    """Detects references to report, medication, reminder, appointment, doctor profiles, etc."""

    def __init__(
        self,
        report_service: ReportService,
        reminder_service: ReminderService,
        appointment_service: AppointmentService,
        prescription_service: PrescriptionService,
        doctor_service: DoctorProfileService,
        database: Any = None
    ):
        self.report_service = report_service
        self.reminder_service = reminder_service
        self.appointment_service = appointment_service
        self.prescription_service = prescription_service
        self.doctor_service = doctor_service
        self.db = database
        self.patient_memory_col = database.patient_memory if database is not None else None

    async def resolve_context(self, patient_id: str, message: str) -> Dict[str, Any]:
        """Resolves context and retrieves relevant DB objects"""
        resolved = {}
        msg_lower = message.lower()

        # 1. Reports detection
        if any(kw in msg_lower for kw in ["report", "ocr", "upload", "record"]):
            try:
                reports = await self.report_service.list_reports_by_patient(patient_id, limit=5)
                if reports:
                    resolved["reports"] = reports
            except Exception as e:
                logger.error(f"Resolver failed to fetch reports: {e}")

        # 2. Medications & Prescriptions & Drug Safety detection
        if any(kw in msg_lower for kw in ["medicine", "prescription", "medication", "pill", "drug", "safety", "interaction"]):
            try:
                prescriptions = await self.prescription_service.list_prescriptions_by_patient(patient_id, limit=5)
                if prescriptions:
                    resolved["prescriptions"] = prescriptions
                
                # Fetch safety / validation summary from patient memory
                if self.patient_memory_col is not None:
                    memory_doc = await self.patient_memory_col.find_one({"patient_id": patient_id})
                    if memory_doc and "validation_summary" in memory_doc:
                        resolved["drug_safety"] = memory_doc["validation_summary"]
            except Exception as e:
                logger.error(f"Resolver failed to fetch prescriptions/safety: {e}")

        # 3. Reminders detection
        if any(kw in msg_lower for kw in ["reminder", "remind", "schedule", "alarm"]):
            try:
                reminders = await self.reminder_service.list_reminders_by_patient(patient_id, limit=5)
                if reminders:
                    resolved["reminders"] = reminders
            except Exception as e:
                logger.error(f"Resolver failed to fetch reminders: {e}")

        # 4. Appointments & Doctors detection (Strict Context Disentanglement)
        is_doctor_discovery = (
            any(kw in msg_lower for kw in ["suggest", "recommend", "find doctor", "find a doctor", "list doctor", "which doctor", "who should i see", "doctor for", "specialist for"]) or
            ("doctor" in msg_lower and any(act in msg_lower for act in ["suggest", "recommend", "find", "get", "need", "looking"])) or
            any(spec in msg_lower for spec in ["cardiologist", "dermatologist", "neurologist", "pediatrician", "orthopedic", "physician"])
        )

        is_appointment_query = (
            any(kw in msg_lower for kw in ["my appointment", "my appointments", "my booked", "booked appointment", "active appointment", "active appointments", "upcoming appointment", "scheduled appointment", "appointment history", "cancel appointment", "reschedule appointment"]) or
            any(typo in msg_lower for typo in ["active appoiment", "active appoiments", "my appoiments", "my appoiment", "appoiments", "appoiment"]) or
            ("appointment" in msg_lower and not is_doctor_discovery)
        )

        if is_doctor_discovery:
            try:
                target_specialty = detect_specialty_from_query(message)
                if hasattr(self.doctor_service, "list_verified_doctors_with_names"):
                    doctors = await self.doctor_service.list_verified_doctors_with_names(limit=5, specialization=target_specialty)
                else:
                    doctors = await self.doctor_service.search_verified_doctors(specialty=target_specialty)
                if doctors:
                    resolved["doctors"] = doctors
            except Exception as e:
                logger.error(f"Resolver failed to fetch doctors: {e}")

        elif is_appointment_query:
            try:
                is_active_explicit = any(kw in msg_lower for kw in ["active", "future", "upcoming", "scheduled", "open", "pending"])
                is_history_explicit = any(kw in msg_lower for kw in ["past", "history", "completed", "previous"])

                if is_active_explicit:
                    filter_active = True
                elif is_history_explicit:
                    filter_active = False
                else:
                    filter_active = True

                appointments = await self.appointment_service.list_appointments_by_patient(
                    patient_id, limit=5, active_only=filter_active
                )
                if appointments:
                    resolved["appointments"] = appointments
            except Exception as e:
                logger.error(f"Resolver failed to fetch appointments: {e}")

        # 5. Lab values & Risks detection
        if any(kw in msg_lower for kw in ["lab", "value", "result", "cholesterol", "diabetes", "blood test", "sugar", "risk", "finding", "recommendation"]):
            try:
                # Latest reports with parsed lab results or risk findings
                reports = await self.report_service.list_reports_by_patient(patient_id, limit=10)
                
                lab_reports = [r for r in reports if r.laboratory_results]
                if lab_reports:
                    resolved["laboratory_results"] = lab_reports[0].laboratory_results
                    resolved["lab_report_id"] = lab_reports[0].id
                
                risk_reports = [r for r in reports if r.risk_findings]
                if risk_reports:
                    resolved["risks"] = risk_reports[0].risk_findings
                    resolved["risk_report_id"] = risk_reports[0].id
            except Exception as e:
                logger.error(f"Resolver failed to fetch lab/risk data: {e}")

        return resolved
