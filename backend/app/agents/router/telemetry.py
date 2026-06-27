"""
Nura - Router Telemetry
Tracks routing requests metrics, latency distributions, and fallback frequencies.
"""

from typing import Dict, Any
from app.agents.router.confidence import get_confidence_level, ConfidenceLevel


class RouterTelemetryTracker:
    """Telemetry metrics tracker for platform Router Agent operations"""

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        """Reset all counters to zero"""
        self._total_requests: int = 0
        self._total_latency_ms: float = 0.0
        
        self._confidence_distribution: Dict[str, int] = {
            ConfidenceLevel.HIGH: 0,
            ConfidenceLevel.MEDIUM: 0,
            ConfidenceLevel.LOW: 0
        }
        
        self._intent_distribution: Dict[str, int] = {
            "GREETING": 0,
            "GENERAL_CHAT": 0,
            "MEDICAL_QUESTION": 0,
            "SYMPTOM_ANALYSIS": 0,
            "REPORT_ANALYSIS": 0,
            "DRUG_INTERACTION": 0,
            "DOCTOR_RECOMMENDATION": 0,
            "REMINDER": 0,
            "APPOINTMENT": 0,
            "CONVERSATION_RECALL": 0,
            "UNKNOWN": 0
        }
        
        self._total_fallbacks: int = 0
        self._total_failures: int = 0

    def record_routing(
        self,
        intent: str,
        confidence: float,
        latency_ms: float,
        is_fallback: bool,
        is_failure: bool = False
    ) -> None:
        """Accumulate parameters for a routing event"""
        self._total_requests += 1
        self._total_latency_ms += latency_ms
        
        if is_failure:
            self._total_failures += 1
            return

        # Record intent distribution
        upper_intent = intent.upper().strip()
        if upper_intent in self._intent_distribution:
            self._intent_distribution[upper_intent] += 1
        else:
            self._intent_distribution["UNKNOWN"] += 1

        # Record confidence tier level
        conf_level = get_confidence_level(confidence)
        self._confidence_distribution[conf_level] += 1

        if is_fallback:
            self._total_fallbacks += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Compile and return formatted telemetry metrics report"""
        total = self._total_requests
        avg_latency = (self._total_latency_ms / total) if total > 0 else 0.0
        
        unknown_count = self._intent_distribution.get("UNKNOWN", 0)
        unknown_pct = (unknown_count / total * 100.0) if total > 0 else 0.0
        fallback_pct = (self._total_fallbacks / total * 100.0) if total > 0 else 0.0
        
        return {
            "total_routed_requests": total,
            "average_routing_latency_ms": round(avg_latency, 2),
            "confidence_distribution": dict(self._confidence_distribution),
            "intent_distribution": dict(self._intent_distribution),
            "unknown_queries_count": unknown_count,
            "unknown_percentage": round(unknown_pct, 2),
            "fallback_count": self._total_fallbacks,
            "fallback_percentage": round(fallback_pct, 2),
            "routing_failures_count": self._total_failures
        }


# Global Singleton instance
_telemetry_instance = RouterTelemetryTracker()


def get_router_telemetry() -> RouterTelemetryTracker:
    """Retrieve singleton instance of RouterTelemetryTracker"""
    return _telemetry_instance
