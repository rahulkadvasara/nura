"""
Nura - Intent Detection Service
Wrapper leveraging IntentClassifier for unified, deterministic query intent classification.
"""

import logging
from typing import Dict, Tuple
from app.agents.router.intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)


class IntentDetectionService:
    """Delegating wrapper for IntentClassifier providing query caching and scoring telemetry"""

    def __init__(self):
        self.classifier = IntentClassifier()

    def detect_intent(self, query: str) -> str:
        """Detect intent from query string and return winning intent string"""
        intent, _ = self.detect_intent_with_scores(query)
        return intent

    def detect_intent_with_scores(self, query: str) -> Tuple[str, Dict[str, float]]:
        """
        Analyze query and return winning intent along with match scores dictionary.
        Leverages IntentClassifier for consistent classification across pre-fetching and routing.
        """
        if not query or not query.strip():
            return "UNKNOWN", {"UNKNOWN": 0.0}

        # 0. Check Cache
        try:
            from app.services.rag_cache_service import get_rag_cache_service
            cache_svc = get_rag_cache_service()
            cached = cache_svc.get_query(query)
            if cached is not None:
                return cached[0], cached[1]
        except Exception:
            cache_svc = None

        # 1. Classify intent via router IntentClassifier
        res = self.classifier.classify(query)
        winner = res.intent
        scores = res.candidate_intents

        if cache_svc is not None:
            try:
                cache_svc.set_query(query, winner, scores)
            except Exception:
                pass

        return winner, scores


def get_intent_detection_service() -> IntentDetectionService:
    """Dependency injection provider for IntentDetectionService"""
    return IntentDetectionService()

