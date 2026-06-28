from typing import List

class RecommendationBuilder:
    """Builds deterministic, non-LLM recommendations based on overall interaction severity."""

    RECOMMENDATIONS_MAP = {
        "HIGH": [
            "Avoid combination.",
            "Immediate physician review recommended."
        ],
        "MEDIUM": [
            "Use with caution.",
            "Consult physician."
        ],
        "LOW": [
            "Monitor patient."
        ],
        "UNKNOWN": [
            "Interaction details are unknown.",
            "Consult physician to verify safety."
        ],
        "NONE": [
            "No known interactions detected.",
            "Proceed with normal instructions."
        ]
    }

    @classmethod
    def build(cls, severity: str) -> List[str]:
        """
        Return a list of deterministic recommendations for the given overall severity.
        """
        s = severity.upper() if severity else "NONE"
        return cls.RECOMMENDATIONS_MAP.get(s, cls.RECOMMENDATIONS_MAP["NONE"])
