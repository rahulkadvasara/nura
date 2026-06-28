"""
Nura - Clinical Summarization Mapping Service
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("nura.report_ai.summary_service")


class SummaryService:
    """Formats clinical summaries and generates default educational fallback descriptions if LLM fails"""

    def generate_fallback_summaries(
        self,
        demographics: Dict[str, Any],
        labs: List[Dict[str, Any]],
        risk_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Constructs clinical summaries from rule findings if LLM fails"""
        patient_name = demographics.get("patient_name") or "the patient"
        age = demographics.get("age")
        gender = demographics.get("gender")
        dem_str = f"for {patient_name}"
        if age or gender:
            dem_str += f" ({', '.join(filter(None, [str(age) + ' y/o' if age else '', gender]))})"

        abnormal_labs = [l for l in labs if l.get("is_abnormal")]
        
        # 1. Executive Summary
        if not abnormal_labs:
            ai_summary = f"Executive Overview: Medical report review {dem_str} indicates all analyzed laboratory values are within standard clinical reference ranges."
        else:
            names = [l["test_name"] for l in abnormal_labs[:3]]
            ai_summary = (
                f"Executive Overview: Medical report review {dem_str} reveals "
                f"{len(abnormal_labs)} abnormal parameter(s), specifically: {', '.join(names)}. "
                f"Clinical risk findings indicate potential health flags."
            )

        # 2. Patient summary
        if not abnormal_labs:
            patient_summary = (
                "Your medical report results are all within the normal ranges. "
                "This indicates that your tested health markers are stable. "
                "Continue maintaining a healthy lifestyle and schedule standard repeat checks as advised by your physician."
            )
        else:
            lines = []
            for f in risk_findings[:3]:
                lines.append(f"- {f.get('finding_name')}: {f.get('message')}")
            
            patient_summary = (
                f"Your medical report shows some out-of-range parameters. Specifically, we noted:\n"
                + "\n".join(lines) + "\n\n"
                "Please discuss these results with your doctor. They will help explain if these require any treatment or further diagnostic monitoring."
            )

        # 3. Doctor summary
        if not abnormal_labs:
            doctor_summary = (
                f"Diagnostic review of laboratory panels {dem_str} demonstrates metabolic and physiological stability. "
                "No clinically significant rule exclusions triggered. Recommend routine tracking."
            )
        else:
            lines = []
            for f in risk_findings:
                lines.append(f"- {f.get('finding_name')} (Severity: {f.get('severity')}): {f.get('message')}")
                
            doctor_summary = (
                f"Clinical evaluation of laboratory panels {dem_str} flags diagnostic markers: \n"
                + "\n".join(lines) + "\n\n"
                "Differential diagnostic monitoring is indicated for the highlighted organ systems."
            )

        return {
            "ai_summary": ai_summary,
            "patient_summary": patient_summary,
            "doctor_summary": doctor_summary,
            "confidence": 0.65
        }
