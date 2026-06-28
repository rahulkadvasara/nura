"""
Nura - Patient Memory Builder for Report Sync
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.patient_memory import PatientMemoryInDB, PatientMemoryUpdate, PatientMemoryCreate
from app.models.report import ReportInDB
from app.repositories.patient_memory_repository import PatientMemoryRepository
from app.services.patient_summary_builder import PatientSummaryBuilder

logger = logging.getLogger("nura.report_sync.patient_memory_builder")


class ReportPatientMemoryBuilder:
    """Helper to incrementally update PatientMemory in MongoDB based on newly processed reports"""

    def __init__(
        self,
        patient_memory_repository: PatientMemoryRepository,
        patient_summary_builder: PatientSummaryBuilder
    ):
        self.patient_memory_repository = patient_memory_repository
        self.patient_summary_builder = patient_summary_builder

    async def build_incremental_memory(
        self,
        patient_id: str,
        report: ReportInDB
    ) -> PatientMemoryCreate:
        """Incrementally updates patient memory fields while maintaining chronological logs"""
        existing = await self.patient_memory_repository.get_by_patient_id(patient_id)
        
        # Build baseline summary using existing aggregator service (longitudinal AI summaries)
        baseline = await self.patient_summary_builder.build_summary(patient_id)

        # Initialize defaults if no memory document exists yet
        chronic_conditions = list(baseline.chronic_conditions)
        allergies = list(baseline.allergies)
        medications = list(baseline.medications)
        surgeries = list(baseline.surgeries)
        diagnoses = list(baseline.diagnoses)
        health_risks = list(baseline.health_risks)
        recent_findings = list(baseline.recent_findings)
        lifestyle_notes = baseline.lifestyle_notes
        timeline = list(baseline.timeline)

        lab_history = []
        med_history = []
        diag_history = []
        rep_summaries = []
        lab_trends_text = ""

        if existing:
            lab_history = list(existing.laboratory_history or [])
            med_history = list(existing.medication_history or [])
            diag_history = list(existing.diagnosis_history or [])
            rep_summaries = list(existing.report_summaries or [])
            lab_trends_text = existing.laboratory_trends or ""

        # Safe extract report timestamp
        report_date = report.created_at
        if not report_date:
            report_date = datetime.now(timezone.utc)
        report_date_str = report_date.isoformat() if isinstance(report_date, datetime) else str(report_date)

        # 1. Update laboratory history
        report_labs = getattr(report, "laboratory_results", []) or []
        for lab in report_labs:
            # Check for duplicate parameter in same report
            exists = any(
                item.get("test_name") == lab.get("test_name") and item.get("report_id") == report.id
                for item in lab_history
            )
            if not exists:
                lab_history.append({
                    "test_name": lab.get("test_name"),
                    "value": lab.get("value"),
                    "unit": lab.get("unit"),
                    "status": lab.get("status", "NORMAL"),
                    "report_date": report_date_str,
                    "report_id": report.id
                })

        # 2. Update medications history
        report_meds = getattr(report, "medications", []) or []
        for med in report_meds:
            exists = any(
                item.get("medicine") == med.get("medicine") and item.get("report_id") == report.id
                for item in med_history
            )
            if not exists:
                med_history.append({
                    "medicine": med.get("medicine"),
                    "dosage": med.get("dosage"),
                    "frequency": med.get("frequency"),
                    "duration": med.get("duration"),
                    "route": med.get("route"),
                    "report_date": report_date_str,
                    "report_id": report.id
                })

        # 3. Update diagnosis history
        report_diags = getattr(report, "diagnoses", []) or []
        for diag in report_diags:
            exists = any(
                item.get("diagnosis") == diag and item.get("report_id") == report.id
                for item in diag_history
            )
            if not exists:
                diag_history.append({
                    "diagnosis": diag,
                    "report_date": report_date_str,
                    "report_id": report.id
                })

        # 4. Update report summaries log
        if report.ai_summary:
            exists = any(item.get("report_id") == report.id for item in rep_summaries)
            if not exists:
                rep_summaries.append({
                    "report_id": report.id,
                    "report_type": str(report.report_type),
                    "ai_summary": report.ai_summary,
                    "summary_confidence": getattr(report, "summary_confidence", 0.90),
                    "generated_at": report_date_str
                })

        # Sort histories chronologically by report date
        def get_date_key(item):
            return item.get("report_date", "")

        lab_history.sort(key=get_date_key)
        med_history.sort(key=get_date_key)
        diag_history.sort(key=get_date_key)
        rep_summaries.sort(key=get_date_key)

        # 5. Formulate text trends summary
        trend_lines = []
        for t_name in set(item["test_name"] for item in lab_history if item.get("test_name")):
            t_items = [item for item in lab_history if item["test_name"] == t_name]
            if len(t_items) > 1:
                vals = [f"{item['value']}{item.get('unit','') or ''} on {item['report_date'][:10]}" for item in t_items]
                trend_lines.append(f"{t_name} trend: {', '.join(vals)}")
        
        if trend_lines:
            lab_trends_text = "; ".join(trend_lines[:5])
        else:
            lab_trends_text = "No laboratory trends detected yet."

        # 6. Ensure timeline includes this report
        exists_timeline = any(item.get("ref_id") == report.id for item in timeline)
        if not exists_timeline:
            timeline.append({
                "type": "report",
                "description": f"Medical Report Uploaded ({report.report_type})",
                "timestamp": report_date_str,
                "ref_id": report.id
            })
            timeline.sort(key=get_timestamp_key, reverse=True)

        return PatientMemoryCreate(
            patient_id=patient_id,
            ai_summary=baseline.ai_summary,
            longitudinal_summary=baseline.ai_summary,
            chronic_conditions=chronic_conditions,
            allergies=allergies,
            medications=medications,
            surgeries=surgeries,
            diagnoses=diagnoses,
            health_risks=health_risks,
            recent_findings=recent_findings,
            lifestyle_notes=lifestyle_notes,
            timeline=timeline,
            latest_report_summary=report.ai_summary,
            latest_risk=f"{report.overall_risk} ({report.risk_score})" if report.overall_risk else None,
            latest_recommendations=report.recommendations or [],
            laboratory_history=lab_history,
            medication_history=med_history,
            diagnosis_history=diag_history,
            laboratory_trends=lab_trends_text,
            procedures=getattr(existing, "procedures", []) or [],
            medical_history=getattr(existing, "medical_history", []) or [],
            report_summaries=rep_summaries
        )


def get_timestamp_key(item):
    ts = item.get("timestamp")
    return ts if ts else ""
