"""
Nura - Confidence Evaluator
Classifies intent scores into HIGH, MEDIUM, and LOW confidence tiers.
"""

from app.core.ai_config import ai_settings


class ConfidenceLevel:
    """Tiers for categorization of confidence calculations"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def get_confidence_level(confidence: float) -> str:
    """
    Categorize numeric confidence rating into HIGH, MEDIUM, or LOW tier levels
    based on active platform router thresholds configurations.
    """
    if confidence >= ai_settings.ROUTER_CONFIDENCE_HIGH:
        return ConfidenceLevel.HIGH
    elif confidence >= ai_settings.ROUTER_CONFIDENCE_MEDIUM:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW
