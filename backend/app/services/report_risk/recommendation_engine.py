"""
Nura - Structured Recommendations Generator
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger("nura.report_risk.recommendation_engine")


class RecommendationEngine:
    """Generates educational clinical recommendations based on abnormal results and diagnostic rules findings"""

    DISCLAIMER = "This recommendation is strictly for educational purposes and is not a substitute for professional medical advice."

    def generate_recommendations(self, findings: List[Dict[str, Any]], critical_count: int) -> List[Dict[str, Any]]:
        """Maps findings to structured recommendations.
        
        Returns a list of dicts:
        - recommendation_type: Repeat laboratory test, Consult physician, Emergency attention, Lifestyle modification, Medication review, Specialist referral
        - description: str
        - urgency: ROUTINE, SOON, IMMEDIATE
        - disclaimer: str
        """
        recommendations = []
        types_added = set()

        # 1. Check for critical alarms (Emergency)
        if critical_count > 0:
            recommendations.append({
                "recommendation_type": "Emergency attention",
                "description": "One or more values represent critical laboratory alarm ranges. Contact a physician immediately or visit an urgent care center.",
                "urgency": "IMMEDIATE",
                "disclaimer": self.DISCLAIMER
            })
            types_added.add("Emergency attention")

        # 2. Map rules findings to standard types
        for f in findings:
            flag = f.get("flag", "")
            severity = f.get("severity", "LOW")

            # Consult physician
            if severity in ("HIGH", "CRITICAL") and "Consult physician" not in types_added:
                recommendations.append({
                    "recommendation_type": "Consult physician",
                    "description": f"Schedule a clinical evaluation with your primary care provider to discuss significant findings.",
                    "urgency": "SOON",
                    "disclaimer": self.DISCLAIMER
                })
                types_added.add("Consult physician")

            # Diabetes
            if flag == "DIABETES_MARKER":
                if "Lifestyle modification" not in types_added:
                    recommendations.append({
                        "recommendation_type": "Lifestyle modification",
                        "description": "Discuss glucose monitoring, dietary alterations, and physical activities modifications with a qualified nutritionist or physician.",
                        "urgency": "ROUTINE",
                        "disclaimer": self.DISCLAIMER
                    })
                    types_added.add("Lifestyle modification")
                if severity in ("HIGH", "CRITICAL") and "Specialist referral" not in types_added:
                    recommendations.append({
                        "recommendation_type": "Specialist referral",
                        "description": "Request a referral to an endocrinologist for comprehensive glycemic management evaluation.",
                        "urgency": "SOON",
                        "disclaimer": self.DISCLAIMER
                    })
                    types_added.add("Specialist referral")

            # Kidney function
            if flag == "KIDNEY_RISK":
                if "Specialist referral" not in types_added and severity in ("HIGH", "CRITICAL"):
                    recommendations.append({
                        "recommendation_type": "Specialist referral",
                        "description": "Consider consultation with a nephrologist to evaluate reduced glomerular filtration rates.",
                        "urgency": "SOON",
                        "disclaimer": self.DISCLAIMER
                    })
                    types_added.add("Specialist referral")
                if "Medication review" not in types_added:
                    recommendations.append({
                        "recommendation_type": "Medication review",
                        "description": "Review list of active drugs (specifically nephrotoxic agents like NSAIDs) with a pharmacist or physician.",
                        "urgency": "ROUTINE",
                        "disclaimer": self.DISCLAIMER
                    })
                    types_added.add("Medication review")

            # Lipids
            if flag == "LIPID_ABNORMALITY":
                if "Lifestyle modification" not in types_added:
                    recommendations.append({
                        "recommendation_type": "Lifestyle modification",
                        "description": "Incorporate a low-cholesterol diet and heart-healthy cardiovascular activities into your routine.",
                        "urgency": "ROUTINE",
                        "disclaimer": self.DISCLAIMER
                    })
                    types_added.add("Lifestyle modification")
                if severity in ("HIGH", "CRITICAL") and "Consult physician" not in types_added:
                    recommendations.append({
                        "recommendation_type": "Consult physician",
                        "description": "Consult a cardiologist or primary care provider to evaluate cardiovascular risk profiles and discuss lipid-lowering therapies.",
                        "urgency": "ROUTINE",
                        "disclaimer": self.DISCLAIMER
                    })
                    types_added.add("Consult physician")

        # 3. Default recommendation if abnormal findings exist but no specific rule matched
        if findings and not recommendations:
            recommendations.append({
                "recommendation_type": "Consult physician",
                "description": "Review abnormal laboratory parameters with a licensed healthcare practitioner.",
                "urgency": "ROUTINE",
                "disclaimer": self.DISCLAIMER
            })
            
        # 4. Standard follow-up retest recommendation
        if findings:
            recommendations.append({
                "recommendation_type": "Repeat laboratory test",
                "description": "Repeat abnormal laboratory panels in 2 to 4 weeks or as advised by your physician to track parameters trends.",
                "urgency": "ROUTINE",
                "disclaimer": self.DISCLAIMER
            })

        return recommendations
