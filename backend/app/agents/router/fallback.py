"""
Nura - Fallback Manager
Ensures unmapped, empty, or ambiguous queries resolve safely to UnknownAgent.
"""

from typing import Dict, List
from app.agents.router.schemas import RoutingDecision
from app.agents.router.intent_registry import get_intent_registry


class FallbackManager:
    """Manages fallback routing parameters to prevent exceptions and route gracefully"""

    @staticmethod
    def get_fallback_decision(matched_rules: List[str] = None) -> RoutingDecision:
        """Construct fallback routing decision pointing to default UnknownAgent"""
        rules = matched_rules or ["fallback:default_catchall"]
        registry = get_intent_registry()
        unknown_agent = registry.get_agent("UNKNOWN") or "UnknownAgent"

        return RoutingDecision(
            selected_agent=unknown_agent,
            detected_intent="UNKNOWN",
            confidence=0.0,
            matched_rules=rules
        )

    @staticmethod
    def is_ambiguous(candidate_intents: Dict[str, float]) -> bool:
        """
        Check if classification is ambiguous.
        Ambiguity occurs if multiple candidate intents share identical highest non-zero scores.
        """
        if len(candidate_intents) <= 1:
            return False

        # Sort candidate scores descending
        sorted_candidates = sorted(candidate_intents.items(), key=lambda item: item[1], reverse=True)
        top_intent, top_score = sorted_candidates[0]
        second_intent, second_score = sorted_candidates[1]

        # If top scores are identical and non-zero, it is ambiguous
        if top_score > 0.0 and top_score == second_score:
            return True
            
        return False
