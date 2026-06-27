"""
Nura - Clinical Risk Scoring and Analysis Engine
"""

import json
import logging
from typing import List, Dict, Any, Tuple
from app.services.ai_service import AIService

logger = logging.getLogger("nura.report_risk.risk_engine")


class RiskEngine:
    """Computes overall risk score and matches AI-assisted justifications for clinical findings"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    def calculate_score_and_severity(self, rule_findings: List[Dict[str, Any]], critical_labs_count: int) -> Tuple[float, str]:
        """Calculates risk score (0.0 to 100.0) and overall risk category"""
        score = 0.0
        
        # Accumulate score weights from rule findings
        has_critical = critical_labs_count > 0
        has_high = False
        has_medium = False
        has_low = False

        for f in rule_findings:
            sev = f.get("severity", "LOW").upper()
            if sev == "CRITICAL":
                score += 35.0
                has_critical = True
            elif sev == "HIGH":
                score += 25.0
                has_high = True
            elif sev == "MEDIUM":
                score += 15.0
                has_medium = True
            elif sev == "LOW":
                score += 7.0
                has_low = True

        # Cap score at 100.0
        score = min(100.0, score)

        # Classify overall risk level
        if has_critical or score >= 60.0:
            severity = "CRITICAL"
        elif has_high or score >= 40.0:
            severity = "HIGH"
        elif has_medium or score >= 20.0:
            severity = "MEDIUM"
        elif has_low or score > 0.0:
            severity = "LOW"
        else:
            severity = "NORMAL"

        return score, severity

    async def analyze_risks(self, ocr_text: str, rule_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Queries AIService to generate explanation justifications for the clinical findings.
        
        Returns dict containing:
        - findings_explanations: List[Dict[str, str]]
        - confidence: float
        """
        if not rule_findings:
            return {
                "findings_explanations": [],
                "confidence": 1.0
            }

        # 1. Attempt AI analysis explanations
        try:
            findings_summary = "\n".join([
                f"- Name: {f['rule_name']} | Severity: {f['severity']} | Parameter alert details: {f['message']}"
                for f in rule_findings
            ])
            
            system_prompt = (
                "You are an expert diagnostic risk analysis coordinator. Review the listed clinical rule findings "
                "from a patient's medical report and output a professional clinical explanation for each finding. "
                "Keep descriptions focused, explaining the clinical significance of values. "
                "Do NOT write any overall patient summaries, summaries of the report, greeting text, or advice.\n\n"
                "Respond ONLY with a valid JSON object matching this schema:\n"
                "{\n"
                '  "findings_explanations": [\n'
                "    {\n"
                '      "finding_name": "string (MUST exactly match finding name from inputs)",\n'
                '      "explanation": "string (professional clinical explanation of the finding)"\n'
                "    }\n"
                "  ],\n"
                '  "confidence": 0.95\n'
                "}"
            )
            
            res = await self.ai_service.generate_json(
                prompt=f"Triggered clinical findings:\n\n{findings_summary}",
                system_prompt=system_prompt,
                temperature=0.0
            )
            
            parsed = json.loads(res.response)
            return {
                "findings_explanations": parsed.get("findings_explanations") or [],
                "confidence": float(parsed.get("confidence", 0.90))
            }
        except Exception as e:
            logger.warning(f"LLM risk explanations generation failed: {e}. Executing default descriptions fallback.")

        # 2. Local fallback rule-based mapping (construct default explanations)
        explanations = []
        for f in rule_findings:
            explanations.append({
                "finding_name": f["rule_name"],
                "explanation": f"Abnormal laboratory parameters triggered standard clinical rule criteria for {f['rule_name']}: {f['message']}"
            })
            
        return {
            "findings_explanations": explanations,
            "confidence": 0.70
        }
