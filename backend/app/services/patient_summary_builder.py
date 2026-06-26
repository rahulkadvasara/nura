"""
Nura - Patient Summary Builder Service
Compiles longitudinal patient summaries from various database sources
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.models.patient_memory import PatientMemoryCreate
from app.repositories.user_repository import UserRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.health_insight_repository import HealthInsightRepository
from app.repositories.appointment_repository import AppointmentRepository

logger = logging.getLogger("nura.services.patient_summary_builder")


class PatientSummaryBuilder:
    """Service to aggregate data and build structured patient memory summaries"""

    def __init__(
        self,
        user_repository: UserRepository,
        report_repository: ReportRepository,
        consultation_repository: ConsultationRepository,
        prescription_repository: PrescriptionRepository,
        health_insight_repository: HealthInsightRepository,
        appointment_repository: AppointmentRepository,
    ):
        self.user_repository = user_repository
        self.report_repository = report_repository
        self.consultation_repository = consultation_repository
        self.prescription_repository = prescription_repository
        self.health_insight_repository = health_insight_repository
        self.appointment_repository = appointment_repository

    async def build_summary(self, patient_id: str) -> PatientMemoryCreate:
        """
        Gathers patient information across different collections and compiles
        a unified PatientMemoryCreate object.
        """
        logger.info(f"Building summary for patient: {patient_id}")

        # 1. Fetch raw user profile to catch any dynamic fields (like allergies, surgeries, lifestyle_notes)
        raw_user: Dict[str, Any] = {}
        try:
            db_id = ObjectId(patient_id) if ObjectId.is_valid(patient_id) else patient_id
            doc = await self.user_repository.collection.find_one({"_id": db_id})
            if doc:
                raw_user = doc
        except Exception as e:
            logger.warning(f"Error fetching raw user profile for patient {patient_id}: {str(e)}")

        full_name = raw_user.get("full_name", "Patient")
        
        # Mapped from patient profile fields
        allergies: List[str] = raw_user.get("allergies", [])
        if isinstance(allergies, str):
            allergies = [a.strip() for a in allergies.split(",") if a.strip()]
        elif not isinstance(allergies, list):
            allergies = []

        surgeries: List[str] = raw_user.get("surgeries", [])
        if isinstance(surgeries, str):
            surgeries = [s.strip() for s in surgeries.split(",") if s.strip()]
        elif not isinstance(surgeries, list):
            surgeries = []

        lifestyle_notes: Optional[str] = raw_user.get("lifestyle_notes")

        # 2. Fetch and aggregate reports
        reports = await self.report_repository.get_many({"patient_id": patient_id}, limit=100)
        reports.sort(key=lambda r: r.created_at if hasattr(r, "created_at") else datetime.min, reverse=True)

        recent_findings: List[str] = []
        report_conditions: List[str] = []
        
        for report in reports:
            # Capture recent findings from completed report AI summaries
            if report.processing_status == "completed" and report.ai_summary:
                if len(recent_findings) < 5:
                    recent_findings.append(report.ai_summary)
            
            # Extract flags/conditions from structured data or entities
            if report.structured_data:
                # Look for common condition/chronic keys
                for key in ["conditions", "chronic_conditions", "findings"]:
                    val = report.structured_data.get(key)
                    if isinstance(val, list):
                        report_conditions.extend([str(item) for item in val])
                    elif isinstance(val, str):
                        report_conditions.append(val)
            
            if report.entities:
                for entity in report.entities:
                    if isinstance(entity, dict):
                        # If entity type is condition or diagnosis
                        ent_type = entity.get("type", "").lower()
                        ent_val = entity.get("value", entity.get("text"))
                        if ent_type in ["condition", "diagnosis", "disease"] and ent_val:
                            report_conditions.append(str(ent_val))

        # 3. Fetch and aggregate consultations
        consultations = await self.consultation_repository.get_many({"patient_id": patient_id}, limit=100)
        consultations.sort(key=lambda c: c.created_at if hasattr(c, "created_at") else datetime.min, reverse=True)

        diagnoses: List[str] = []
        for consult in consultations:
            if consult.diagnosis:
                # Some diagnoses might be comma separated or single strings
                diag_items = [d.strip() for d in consult.diagnosis.split(",") if d.strip()]
                diagnoses.extend(diag_items)

        # 4. Chronic Conditions union
        # Unique union of report conditions and consultation diagnoses
        chronic_conditions_set = set()
        for cond in report_conditions + diagnoses:
            cond_clean = cond.strip().title()
            if cond_clean:
                chronic_conditions_set.add(cond_clean)
        chronic_conditions = sorted(list(chronic_conditions_set))

        # Distinct list of diagnoses
        diagnoses = sorted(list(set([d.strip().title() for d in diagnoses if d.strip()])))

        # 5. Fetch prescriptions and compile active/recent medications
        prescriptions = await self.prescription_repository.get_many({"patient_id": patient_id}, limit=50)
        prescriptions.sort(key=lambda p: p.created_at if hasattr(p, "created_at") else datetime.min, reverse=True)

        medications_set = set()
        for pres in prescriptions:
            if hasattr(pres, "medications") and pres.medications:
                for med in pres.medications:
                    med_str = f"{med.drug_name} {med.dosage}".strip()
                    if med_str:
                        medications_set.add(med_str)
        medications = sorted(list(medications_set))

        # 6. Fetch health insights and compile health risks
        insights = await self.health_insight_repository.get_many({"patient_id": patient_id}, limit=50)
        insights.sort(key=lambda i: i.created_at if hasattr(i, "created_at") else datetime.min, reverse=True)

        health_risks_set = set()
        for insight in insights:
            if insight.severity in ["medium", "high"]:
                risk_str = f"{insight.title}: {insight.description}".strip()
                if risk_str:
                    health_risks_set.add(risk_str)
        health_risks = sorted(list(health_risks_set))

        # 7. Compile timeline of events
        timeline: List[Dict[str, Any]] = []
        
        # Add surgeries to timeline
        for surg in surgeries:
            timeline.append({
                "type": "surgery",
                "description": f"Past Surgery: {surg}",
                "timestamp": None  # Date unspecified from profile
            })

        # Add reports to timeline
        for r in reports[:10]:
            ts = r.created_at.isoformat() if isinstance(r.created_at, datetime) else str(r.created_at)
            timeline.append({
                "type": "report",
                "description": f"Medical Report Uploaded ({r.report_type.value if hasattr(r.report_type, 'value') else str(r.report_type)})",
                "timestamp": ts,
                "ref_id": r.id
            })

        # Add consultations to timeline
        for c in consultations[:10]:
            ts = c.created_at.isoformat() if isinstance(c.created_at, datetime) else str(c.created_at)
            timeline.append({
                "type": "consultation",
                "description": f"Doctor Consultation: {c.diagnosis}",
                "timestamp": ts,
                "ref_id": c.id
            })

        # Sort timeline by timestamp, putting None values at the end or start
        def get_timestamp_key(item):
            ts = item.get("timestamp")
            return ts if ts else ""

        timeline.sort(key=get_timestamp_key, reverse=True)

        # 8. Deterministic AI summary generator
        ai_summary_parts = []
        ai_summary_parts.append(f"Longitudinal health summary for {full_name}.")
        
        if chronic_conditions:
            ai_summary_parts.append(f"Diagnosed chronic conditions: {', '.join(chronic_conditions)}.")
        else:
            ai_summary_parts.append("No active chronic conditions documented.")

        if allergies:
            ai_summary_parts.append(f"Known allergies: {', '.join(allergies)}.")
        else:
            ai_summary_parts.append("No known allergies reported.")

        if medications:
            ai_summary_parts.append(f"Current active medications: {', '.join(medications)}.")
        else:
            ai_summary_parts.append("No active medications documented.")

        if surgeries:
            ai_summary_parts.append(f"Surgical history: {', '.join(surgeries)}.")

        if recent_findings:
            ai_summary_parts.append(f"Recent medical findings summary: {'; '.join(recent_findings[:3])}.")

        ai_summary = " ".join(ai_summary_parts)

        return PatientMemoryCreate(
            patient_id=patient_id,
            ai_summary=ai_summary,
            chronic_conditions=chronic_conditions,
            allergies=allergies,
            medications=medications,
            surgeries=surgeries,
            diagnoses=diagnoses,
            health_risks=health_risks,
            recent_findings=recent_findings,
            lifestyle_notes=lifestyle_notes,
            timeline=timeline
        )
