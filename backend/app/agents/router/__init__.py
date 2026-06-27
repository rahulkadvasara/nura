"""
Nura - Router Agent Package
Includes intent classification, registry mappings, thresholds rules, and fallbacks.
"""

from app.agents.router.schemas import IntentClassificationResult, RoutingDecision
from app.agents.router.intent_registry import IntentRegistry, get_intent_registry
from app.agents.router.intent_classifier import IntentClassifier
from app.agents.router.confidence import get_confidence_level, ConfidenceLevel
from app.agents.router.fallback import FallbackManager
from app.agents.router.routing_rules import RoutingRulesEvaluator
from app.agents.router.telemetry import RouterTelemetryTracker, get_router_telemetry
from app.agents.router.router_agent import RouterAgent

__all__ = [
    "IntentClassificationResult",
    "RoutingDecision",
    "IntentRegistry",
    "get_intent_registry",
    "IntentClassifier",
    "get_confidence_level",
    "ConfidenceLevel",
    "FallbackManager",
    "RoutingRulesEvaluator",
    "RouterTelemetryTracker",
    "get_router_telemetry",
    "RouterAgent"
]
