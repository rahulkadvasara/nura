from typing import List, Dict, Any

class DrugExplanationFallbackService:
    """Fallback generator for drug safety explanations when Groq LLM is unavailable"""

    @staticmethod
    def generate_patient_explanation(severity: str, recommendations: List[str]) -> str:
        rec_str = " ".join(recommendations)
        return (
            f"Interaction Severity: {severity}\n\n"
            f"Reason: Drug interaction detected using clinical interaction database.\n\n"
            f"Recommendation: {rec_str}\n\n"
            f"This drug safety check is for informational purposes only. It is not a substitute for professional "
            f"medical advice, diagnosis, or treatment. Always consult your physician before starting, stopping, "
            f"or changing any medication."
        )

    @staticmethod
    def generate_doctor_explanation(severity: str, recommendations: List[str], interactions: List[Dict[str, Any]]) -> str:
        rec_str = " ".join(recommendations)
        pairs_str = ""
        if interactions:
            pairs_str = "\n".join([
                f"- {p.get('drug_a')} and {p.get('drug_b')} ({p.get('severity')}): {p.get('description')}"
                for p in interactions
            ])
        else:
            pairs_str = "No active interactions recorded."

        return (
            f"Clinical Interaction Report\n"
            f"Severity: {severity}\n"
            f"Database matches:\n{pairs_str}\n\n"
            f"Clinical Recommendation: {rec_str}\n\n"
            f"Suggested actions: Consult clinical database, monitor patient indicators, adjust dosages as appropriate.\n\n"
            f"This drug safety check is for informational purposes only. It is not a substitute for professional "
            f"medical advice, diagnosis, or treatment. Always consult your physician before starting, stopping, "
            f"or changing any medication."
        )

    @staticmethod
    def generate_summary(severity: str, medications: List[str], interactions: List[Dict[str, Any]]) -> str:
        if not interactions:
            return f"No interactions detected between {', '.join(medications)}."
        pairs = [f"{p.get('drug_a')}-{p.get('drug_b')}" for p in interactions]
        return f"Deterministic {severity} interaction detected involving: {', '.join(pairs)}."

    @staticmethod
    def generate_precautions(severity: str) -> str:
        if severity == "HIGH":
            return (
                "- Avoid taking these medications together.\n"
                "- Limit or avoid alcohol and verify food/supplement restrictions with a physician.\n"
                "- Monitor for immediate adverse side-effects (e.g. bleeding, severe dizziness).\n"
                "- Immediate follow-up with your primary physician or emergency care if symptoms present."
            )
        elif severity in ("MEDIUM", "LOW", "UNKNOWN"):
            return (
                "- Use caution when taking these medications together.\n"
                "- Monitor for side-effects and alert your physician if any abnormal symptoms occur.\n"
                "- Separate medication intake times if advised by a healthcare provider.\n"
                "- Schedule routine follow-ups to evaluate therapy progression."
            )
        else:
            return (
                "- Continue taking medications as prescribed.\n"
                "- General warning: limit alcohol intake and maintain balanced nutrition.\n"
                "- Monitor general health indicators.\n"
                "- Routine annual or biannual physician visits recommended."
            )
