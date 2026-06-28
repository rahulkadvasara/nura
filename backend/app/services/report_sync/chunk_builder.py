"""
Nura - Clinical Report Chunk Builder
"""

import logging
from typing import List, Dict, Any
from app.models.report import ReportInDB

logger = logging.getLogger("nura.report_sync.chunk_builder")


class ReportChunkBuilder:
    """Builds clean semantic sentence chunks from processed reports for vector database storage"""

    def build_report_chunks(self, report: ReportInDB) -> List[Dict[str, Any]]:
        """Splits report details into semantic chunks with target section labels.
        
        Returns a list of dicts:
        {
          "text": str,
          "section": str
        }
        """
        chunks = []

        # 1. AI Summaries (Patient & Doctor)
        if report.ai_summary:
            chunks.append({
                "text": f"Executive Summary: {report.ai_summary}",
                "section": "executive_summary"
            })
        if report.patient_summary:
            chunks.append({
                "text": f"Patient Explanation: {report.patient_summary}",
                "section": "patient_summary"
            })
        if report.doctor_summary:
            chunks.append({
                "text": f"Doctor Interpretation: {report.doctor_summary}",
                "section": "doctor_summary"
            })

        # 2. Key Findings
        findings = getattr(report, "key_findings", []) or []
        for f in findings:
            if f:
                chunks.append({
                    "text": f"Key Observation finding: {f}",
                    "section": "key_findings"
                })

        # 3. Clinical Insights
        insights = getattr(report, "clinical_insights", []) or []
        for ins in insights:
            if ins:
                chunks.append({
                    "text": f"Clinical trend insight: {ins}",
                    "section": "clinical_insights"
                })

        # 4. Structured Laboratory Results
        labs = getattr(report, "laboratory_results", []) or []
        for lab in labs:
            name = lab.get("test_name")
            val = lab.get("value")
            unit = lab.get("unit") or ""
            ref = lab.get("reference_range") or ""
            status = lab.get("status") or "NORMAL"
            if name and val is not None:
                chunks.append({
                    "text": f"Laboratory Test Parameter: {name} is {val} {unit} (Reference limit: {ref}, status: {status})",
                    "section": "laboratory_results"
                })

        # 5. Diagnoses
        diags = getattr(report, "diagnoses", []) or []
        for diag in diags:
            if diag:
                chunks.append({
                    "text": f"Clinical Diagnosis: {diag}",
                    "section": "diagnoses"
                })

        # 6. Recommendations
        recs = getattr(report, "recommendations", []) or []
        for rec in recs:
            rec_type = rec.get("recommendation_type")
            desc = rec.get("description")
            urgency = rec.get("urgency", "SOON")
            if rec_type and desc:
                chunks.append({
                    "text": f"Clinical Action suggestion: {rec_type} (Urgency: {urgency}) - {desc}",
                    "section": "recommendations"
                })

        return chunks
