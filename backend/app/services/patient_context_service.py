"""
Nura - Patient Context Service
Business logic for compiling, structuring, and compressing patient contexts from MongoDB
"""

import time
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.user import UserInDB, UserRole
from app.models.patient_memory import PatientMemoryInDB
from app.repositories.user_repository import UserRepository
from app.repositories.patient_memory_repository import PatientMemoryRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.health_insight_repository import HealthInsightRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.schemas.patient_context import PatientContextResponse, PatientContextMetadata

logger = logging.getLogger("nura.ai.context")


class PatientContextService:
    """Service layer for deterministic patient context compilation and token-budget compression"""

    def __init__(
        self,
        user_repository: UserRepository,
        patient_memory_repository: PatientMemoryRepository,
        report_repository: ReportRepository,
        appointment_repository: AppointmentRepository,
        consultation_repository: ConsultationRepository,
        prescription_repository: PrescriptionRepository,
        reminder_repository: ReminderRepository,
        health_insight_repository: HealthInsightRepository,
        chat_session_repository: ChatSessionRepository,
    ):
        self.user_repository = user_repository
        self.patient_memory_repository = patient_memory_repository
        self.report_repository = report_repository
        self.appointment_repository = appointment_repository
        self.consultation_repository = consultation_repository
        self.prescription_repository = prescription_repository
        self.reminder_repository = reminder_repository
        self.health_insight_repository = health_insight_repository
        self.chat_session_repository = chat_session_repository

    def _estimate_tokens(self, data: Dict[str, Any]) -> int:
        """Estimate tokens using len(JSON) / 4 standard character-to-token heuristic"""
        try:
            # Exclude metadata from count to track purely context budget
            dump_data = {k: v for k, v in data.items() if k != "metadata"}
            serialized = json.dumps(dump_data, default=str)
            return len(serialized) // 4
        except Exception:
            return 0

    async def assemble_context(
        self,
        patient_id: str,
        token_budget: int = 4000
    ) -> PatientContextResponse:
        """Assemble the complete structured patient medical context from MongoDB repositories"""
        start_time = time.perf_counter()
        sources_used = set()

        # 1. Fetch User / Patient Profile
        user = await self.user_repository.get(patient_id)
        sources_used.add("users")
        
        patient_profile_dict = None
        if user and user.role == UserRole.PATIENT:
            patient_profile_dict = {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "profile_picture": user.profile_picture,
                "created_at": user.created_at.isoformat() if isinstance(user.created_at, datetime) else user.created_at
            }

        # 2. Fetch patient_memory (highest priority summary info)
        memory = await self.patient_memory_repository.get_by_patient_id(patient_id)
        sources_used.add("patient_memory")

        # 3. Base collection queries (gather all documents first)
        # Reports
        reports_cursor = await self.report_repository.get_many({"patient_id": patient_id}, limit=100)
        sources_used.add("reports")
        reports_cursor.sort(key=lambda x: x.created_at if hasattr(x, "created_at") else datetime.min, reverse=True)

        # Appointments
        appointments_cursor = await self.appointment_repository.get_many({"patient_id": patient_id}, limit=100)
        sources_used.add("appointments")
        appointments_cursor.sort(key=lambda x: (x.slot_date, x.slot_time) if hasattr(x, "slot_date") else ("", ""), reverse=True)

        # Consultations
        consultations_cursor = await self.consultation_repository.get_many({"patient_id": patient_id}, limit=100)
        sources_used.add("consultations")
        consultations_cursor.sort(key=lambda x: x.created_at if hasattr(x, "created_at") else datetime.min, reverse=True)

        # Prescriptions
        prescriptions_cursor = await self.prescription_repository.get_many({"patient_id": patient_id}, limit=100)
        sources_used.add("prescriptions")
        prescriptions_cursor.sort(key=lambda x: x.created_at if hasattr(x, "created_at") else datetime.min, reverse=True)

        # Active Reminders (filter only unresolved reminders)
        reminders_cursor = await self.reminder_repository.get_many({"patient_id": patient_id, "status": "active"}, limit=100)
        sources_used.add("reminders")

        # Recent Health Insights
        insights_cursor = await self.health_insight_repository.get_many({"patient_id": patient_id}, limit=100)
        sources_used.add("health_insights")
        insights_cursor.sort(key=lambda x: x.created_at if hasattr(x, "created_at") else datetime.min, reverse=True)

        # Chat Sessions (metadata only)
        chat_sessions_cursor = await self.chat_session_repository.get_many({"patient_id": patient_id}, limit=100)
        sources_used.add("chat_sessions")

        # 4. Try building the context at different compression levels to fit token budget
        limit_options = [5, 3, 1]
        final_context_dict = {}
        estimated_tokens = 0

        for current_limit in limit_options:
            context_dict = {}
            
            # Static profile mapping
            context_dict["patient_profile"] = patient_profile_dict
            
            # Patient Memory Mapping (Longitudinal values override historical queries)
            if memory:
                context_dict["medical_summary"] = memory.ai_summary
                context_dict["current_conditions"] = list(set(memory.chronic_conditions + memory.diagnoses))
                context_dict["past_medical_history"] = list(set(memory.surgeries + [str(e) for e in memory.timeline]))
                context_dict["current_medications"] = memory.medications
                context_dict["medication_allergies"] = memory.allergies
                context_dict["drug_allergies"] = memory.allergies
                context_dict["lifestyle_notes"] = memory.lifestyle_notes
                context_dict["risk_factors"] = memory.health_risks
            else:
                context_dict["medical_summary"] = None
                context_dict["current_conditions"] = []
                context_dict["past_medical_history"] = []
                context_dict["current_medications"] = []
                context_dict["medication_allergies"] = []
                context_dict["drug_allergies"] = []
                context_dict["lifestyle_notes"] = None
                context_dict["risk_factors"] = []

            # Medication fallback if memory does not supply active meds list
            if not context_dict["current_medications"] and prescriptions_cursor:
                recent_pres = prescriptions_cursor[0]
                context_dict["current_medications"] = [m.drug_name for m in recent_pres.medications] if hasattr(recent_pres, "medications") else []

            # Mapping reports
            reports_list = []
            for r in reports_cursor[:current_limit]:
                reports_list.append({
                    "id": r.id,
                    "report_type": r.report_type.value if hasattr(r.report_type, "value") else str(r.report_type),
                    "risk_level": r.risk_level.value if hasattr(r.risk_level, "value") else str(r.risk_level),
                    "ai_summary": r.ai_summary,
                    "created_at": r.created_at.isoformat() if isinstance(r.created_at, datetime) else r.created_at,
                    "processing_status": r.processing_status.value if hasattr(r.processing_status, "value") else str(r.processing_status),
                })
            context_dict["lab_reports_summary"] = reports_list

            # Mapping appointments
            appt_list = []
            for a in appointments_cursor[:current_limit]:
                appt_list.append({
                    "id": a.id,
                    "doctor_id": a.doctor_id,
                    "slot_date": a.slot_date,
                    "slot_time": a.slot_time,
                    "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                    "reason": a.reason,
                })
            context_dict["appointments_summary"] = appt_list

            # Mapping consultations
            consult_list = []
            for c in consultations_cursor[:current_limit]:
                consult_list.append({
                    "id": c.id,
                    "doctor_id": c.doctor_id,
                    "diagnosis": c.diagnosis,
                    "consultation_notes": c.consultation_notes,
                    "recommendations": c.recommendations,
                    "created_at": c.created_at.isoformat() if isinstance(c.created_at, datetime) else c.created_at,
                })
            context_dict["consultations_summary"] = consult_list

            # Mapping prescriptions
            pres_list = []
            for p in prescriptions_cursor[:current_limit]:
                meds = []
                for m in p.medications:
                    meds.append({
                        "drug_name": m.drug_name,
                        "dosage": m.dosage,
                        "frequency": m.frequency,
                        "duration": m.duration,
                        "instructions": m.instructions
                    })
                pres_list.append({
                    "id": p.id,
                    "doctor_id": p.doctor_id,
                    "medications": meds,
                    "notes": p.notes,
                    "created_at": p.created_at.isoformat() if isinstance(p.created_at, datetime) else p.created_at,
                })
            context_dict["prescriptions_summary"] = pres_list

            # Mapping reminders (always return unresolved reminders within current limit)
            remind_list = []
            for rem in reminders_cursor[:current_limit]:
                remind_list.append({
                    "id": rem.id,
                    "reminder_type": rem.reminder_type.value if hasattr(rem.reminder_type, "value") else str(rem.reminder_type),
                    "title": rem.title,
                    "description": rem.description,
                    "scheduled_time": rem.scheduled_time,
                    "recurrence": rem.recurrence,
                    "status": rem.status.value if hasattr(rem.status, "value") else str(rem.status),
                })
            context_dict["reminder_summary"] = remind_list

            # Mapping health insights
            insights_list = []
            for ins in insights_cursor[:current_limit]:
                insights_list.append({
                    "id": ins.id,
                    "insight_type": ins.insight_type.value if hasattr(ins.insight_type, "value") else str(ins.insight_type),
                    "title": ins.title,
                    "description": ins.description,
                    "severity": ins.severity.value if hasattr(ins.severity, "value") else str(ins.severity),
                    "created_at": ins.created_at.isoformat() if isinstance(ins.created_at, datetime) else ins.created_at,
                })
            context_dict["recent_health_insights"] = insights_list

            # Emergency info calculation (e.g. check if high risk level exists in recent reports)
            high_risk_reports = [r for r in reports_cursor if hasattr(r, "risk_level") and str(r.risk_level) == "high"]
            if high_risk_reports:
                context_dict["emergency_information"] = f"CRITICAL: Patient has {len(high_risk_reports)} reports classified with HIGH risk level."
            else:
                context_dict["emergency_information"] = None

            # Estimate tokens of currently assembled layout
            estimated_tokens = self._estimate_tokens(context_dict)
            final_context_dict = context_dict
            
            # If within budget, break out and finalize
            if estimated_tokens <= token_budget:
                break
        
        # 5. Build Metadata and Response Object
        sections_returned = []
        for section, val in final_context_dict.items():
            if val is not None and val != [] and val != "":
                sections_returned.append(section)

        generated_at = datetime.now(timezone.utc)
        metadata = PatientContextMetadata(
            patient_id=patient_id,
            generated_at=generated_at,
            sources_used=list(sources_used),
            sections_returned=sections_returned,
            estimated_tokens=estimated_tokens,
            context_version="1.0.0"
        )

        final_context_dict["metadata"] = metadata
        response_model = PatientContextResponse(**final_context_dict)

        # 6. Operational Logging (No PHI, only telemetry)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"Assembled patient context for patient {patient_id} in {duration_ms:.1f}ms",
            extra={
                "patient_id": patient_id,
                "build_duration_ms": duration_ms,
                "number_of_sections": len(sections_returned),
                "sources_used": list(sources_used),
                "estimated_tokens": estimated_tokens
            }
        )

        return response_model
