"""
Nura - Clinical Insights and Key Findings Service
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("nura.report_ai.insight_service")


class InsightService:
    """Formats clinical insights, key findings, and generates fallback lists if LLM fails"""

    def generate_fallback_insights(
        self,
        labs: List[Dict[str, Any]],
        risk_findings: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Constructs key findings, clinical insights and patient questions from rule findings if LLM fails"""
        abnormal_labs = [l for l in labs if l.get("is_abnormal")]
        
        # 1. Key Findings
        key_findings = []
        for lab in abnormal_labs[:4]:
            key_findings.append(f"Abnormal {lab['test_name']} value of {lab['value']} {lab.get('unit', '')} (Status: {lab.get('status')})")
        for f in risk_findings[:2]:
            key_findings.append(f"Clinical indicator triggered: {f['finding_name']} ({f['severity']})")
        if not key_findings:
            key_findings.append("All analyzed laboratory markers are within normal references ranges.")

        # 2. Clinical Insights
        clinical_insights = []
        for f in risk_findings:
            flag = f.get("flag", "")
            if flag == "DIABETES_MARKER":
                clinical_insights.append("Glucose metabolism indicators suggest monitoring glycemic control closely to prevent secondary complications.")
            elif flag == "KIDNEY_RISK":
                clinical_insights.append("Renal function filtration indices indicate avoiding nephrotoxic agents and monitoring glomerular filtration.")
            elif flag == "LIVER_ABNORMALITY":
                clinical_insights.append("Liver transaminase elevations suggest reviewing active therapies and monitoring hepatic metabolic panels.")
            elif flag == "ANEMIA_DETECTION":
                clinical_insights.append("Red blood cell indices suggest tracking iron levels, dietary intake, and repeat complete blood count.")
                
        if not clinical_insights:
            clinical_insights.append("Diagnostic parameters show systemic metabolic and biochemical stability. Continue active wellness monitoring.")

        # 3. Follow-up Questions
        followup_questions = [
            "Are there any specific lifestyle or dietary changes that could help normalize my out-of-range results?",
            "Do these findings suggest the need for further diagnostic testing or specialist consultations?",
            "When should I repeat these laboratory investigations to monitor the trends of these parameters?"
        ]
        
        for f in risk_findings[:2]:
            followup_questions.insert(0, f"What does the '{f['finding_name']}' indicator mean for my long-term health?")

        return {
            "key_findings": key_findings[:6],
            "clinical_insights": clinical_insights[:5],
            "followup_questions": followup_questions[:5]
        }
