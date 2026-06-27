"""
Nura - Routing Rules Evaluator
Applies confidence thresholds and registry maps to select winning target agents.
"""

import logging
from app.agents.router.schemas import IntentClassificationResult, RoutingDecision
from app.agents.router.intent_registry import get_intent_registry
from app.agents.router.confidence import get_confidence_level, ConfidenceLevel
from app.agents.router.fallback import FallbackManager

logger = logging.getLogger("nura.router.routing_rules")


class RoutingRulesEvaluator:
    """Evaluator applying threshold constraints to determine winning agent mappings"""

    @staticmethod
    def evaluate_decision(classification: IntentClassificationResult) -> RoutingDecision:
        """Evaluate classification results and select target downstream agent"""
        registry = get_intent_registry()
        
        # 1. Unknown classification intent check
        if classification.intent == "UNKNOWN":
            logger.info("Routing decision: categorized as UNKNOWN. Selecting fallback.")
            return FallbackManager.get_fallback_decision(classification.matched_rules)

        # 2. Check for classification ambiguities
        if FallbackManager.is_ambiguous(classification.candidate_intents):
            logger.warning("Routing decision: ambiguity detected between candidates. Selecting fallback.")
            rules = list(classification.matched_rules) + ["fallback:ambiguous_candidates"]
            return FallbackManager.get_fallback_decision(rules)

        # 3. Categorize confidence level tier
        confidence_level = get_confidence_level(classification.confidence)
        
        if confidence_level == ConfidenceLevel.HIGH:
            # Route immediately to mapped agent
            agent = registry.get_agent(classification.intent) or "UnknownAgent"
            logger.info(f"Routing decision: HIGH confidence ({classification.confidence}). Selected agent: {agent}")
            return RoutingDecision(
                selected_agent=agent,
                detected_intent=classification.intent,
                confidence=classification.confidence,
                matched_rules=classification.matched_rules
            )
            
        elif confidence_level == ConfidenceLevel.MEDIUM:
            # Route to mapped agent of highest candidate
            agent = registry.get_agent(classification.intent) or "UnknownAgent"
            logger.info(f"Routing decision: MEDIUM confidence ({classification.confidence}). Selected agent: {agent}")
            rules = list(classification.matched_rules) + ["routing:medium_confidence_threshold_pass"]
            return RoutingDecision(
                selected_agent=agent,
                detected_intent=classification.intent,
                confidence=classification.confidence,
                matched_rules=rules
            )
            
        else:
            # Low confidence tier -> route to UnknownAgent
            logger.info(f"Routing decision: LOW confidence ({classification.confidence}). Selecting fallback.")
            rules = list(classification.matched_rules) + ["fallback:low_confidence_score"]
            return FallbackManager.get_fallback_decision(rules)
