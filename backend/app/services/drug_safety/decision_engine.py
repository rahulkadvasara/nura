import logging
from typing import List, Dict, Any, Set, Tuple

from app.services.drug_safety.interaction_engine import DrugInteractionEngine
from app.services.drug_safety.severity_classifier import SeverityClassifier
from app.services.drug_safety.recommendation_builder import RecommendationBuilder
from app.services.drug_safety.normalizer import DrugNormalizer
from app.services.drug_safety.models import InteractionPairDetail

logger = logging.getLogger("nura.drug_safety.decision_engine")

class ValidationDecisionEngine:
    """Evaluates validation rules (ALLOW, WARNING, BLOCK) for incoming medications against current medications."""

    def __init__(self, interaction_engine: DrugInteractionEngine, normalizer: DrugNormalizer):
        self.interaction_engine = interaction_engine
        self.normalizer = normalizer

    async def evaluate(self, current_normalized: List[str], incoming_raw: List[str]) -> Dict[str, Any]:
        """
        Evaluate incoming medications against current medications.
        Returns a dictionary containing:
        - decision: 'ALLOW' | 'WARNING' | 'BLOCK'
        - severity: overall highest severity detected
        - detected_interactions: list of matching InteractionPairDetail objects
        - recommendations: list of deterministic recommendations
        """
        # Normalize incoming medications
        incoming_normalized = []
        incoming_map = {} # normalized -> raw
        
        for med in incoming_raw:
            norm = self.normalizer.normalize(med)
            if norm:
                incoming_normalized.append(norm)
                incoming_map[norm] = med

        # Deduplicate incoming normalized list
        incoming_normalized = list(dict.fromkeys(incoming_normalized))

        # Build list of all unique medication names (both current and incoming)
        # We need to evaluate interactions for all pairs where at least one medication is incoming.
        # Why? Because we want to check incoming vs current, and incoming vs incoming!
        # The easiest way is to combine all medications:
        all_meds = list(dict.fromkeys(current_normalized + incoming_normalized))
        
        # Run interaction check on the combined list of medications!
        # We call the existing DrugInteractionEngine to do this deterministically.
        # The engine queries the database, groups interactions, handles bidirectionality,
        # and returns a DrugCheckResponse.
        check_res = await self.interaction_engine.check_interactions(all_meds)

        # Now, we filter detected interactions to only keep those that involve at least one incoming medication.
        # (This avoids reporting existing interactions that are already present in the patient's current medications,
        # although checking all is also safe. Filtering to only report interactions caused by the incoming drug is cleaner
        # and more helpful to show why a drug is blocked/warned).
        relevant_interactions = []
        relevant_severities = []
        incoming_set = set(incoming_normalized)

        for interaction in check_res.detected_interactions:
            # check if drug_a_normalized or drug_b_normalized is in incoming_set
            if interaction.drug_a_normalized in incoming_set or interaction.drug_b_normalized in incoming_set:
                relevant_interactions.append(interaction)
                relevant_severities.append(interaction.severity)

        # Classify severity of relevant interactions
        highest_severity = SeverityClassifier.classify(relevant_severities)

        # Determine decision: ALLOW, WARNING, BLOCK
        if highest_severity == "HIGH":
            decision = "BLOCK"
        elif highest_severity in ("MEDIUM", "LOW", "UNKNOWN"):
            decision = "WARNING"
        else:
            decision = "ALLOW"

        # Build recommendations
        recommendations = RecommendationBuilder.build(highest_severity)

        return {
            "decision": decision,
            "severity": highest_severity,
            "detected_interactions": relevant_interactions,
            "recommendations": recommendations
        }
