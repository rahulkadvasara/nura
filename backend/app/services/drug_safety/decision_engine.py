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

        relevant_interactions: List[InteractionPairDetail] = []
        relevant_severities: List[str] = []

        # 1. Check duplicate active drug hazard
        if incoming_normalized:
            # Check if an incoming drug was ALREADY in current_normalized before adding this new reminder
            for norm in incoming_normalized:
                if norm in current_normalized:
                    raw_name = incoming_map.get(norm, norm).title()
                    dup_detail = InteractionPairDetail(
                        drug_a=raw_name,
                        drug_a_normalized=norm,
                        drug_b=f"{raw_name} (Active)",
                        drug_b_normalized=norm,
                        severity="HIGH",
                        description=f"Duplicate active ingredient hazard: **{raw_name}** is already present in your active medication list. Scheduling duplicate doses increases the risk of accidental overdose, excessive active compound accumulation, mucosal bleeding, and stomach ulceration."
                    )
                    relevant_interactions.append(dup_detail)
                    relevant_severities.append("HIGH")
        else:
            # Profile overview mode (incoming_raw is empty): Check if any active drug appears multiple times
            from collections import Counter
            counts = Counter(current_normalized)
            for norm, count in counts.items():
                if count >= 2:
                    raw_name = norm.title()
                    dup_detail = InteractionPairDetail(
                        drug_a=raw_name,
                        drug_a_normalized=norm,
                        drug_b=f"{raw_name} (Duplicate)",
                        drug_b_normalized=norm,
                        severity="HIGH",
                        description=f"Duplicate active ingredient hazard: Multiple active doses of **{raw_name}** detected in your profile. Scheduling duplicate doses increases the risk of accidental overdose, excessive active compound accumulation, mucosal bleeding, and stomach ulceration."
                    )
                    relevant_interactions.append(dup_detail)
                    relevant_severities.append("HIGH")

        # 2. Build list of unique medication names
        # Remove incoming meds from current list to get truly existing active medications
        existing_normalized = [m for m in current_normalized if m not in incoming_normalized]
        if incoming_normalized:
            all_meds = list(dict.fromkeys(existing_normalized + incoming_normalized))
        else:
            all_meds = list(dict.fromkeys(current_normalized))
        
        # Run interaction check on the combined list of medications
        check_res = await self.interaction_engine.check_interactions(all_meds)

        # 3. Filter detected interactions
        incoming_set = set(incoming_normalized)
        for interaction in check_res.detected_interactions:
            # If incoming_medications were provided, ONLY keep interactions involving an incoming medication!
            # If incoming_medications is empty (profile overview), keep ALL active interactions!
            if not incoming_set or (interaction.drug_a_normalized in incoming_set or interaction.drug_b_normalized in incoming_set):
                key = tuple(sorted([interaction.drug_a_normalized, interaction.drug_b_normalized]))
                if not any(tuple(sorted([i.drug_a_normalized, i.drug_b_normalized])) == key for i in relevant_interactions):
                    relevant_interactions.append(interaction)
                    relevant_severities.append(interaction.severity)

        # Classify overall severity of relevant interactions
        highest_severity = SeverityClassifier.classify(relevant_severities)

        # Determine decision: ALLOW, WARNING, BLOCK
        if highest_severity in ("HIGH", "CRITICAL"):
            decision = "BLOCK"
        elif highest_severity == "MEDIUM":
            decision = "WARNING"
        elif highest_severity in ("LOW", "UNKNOWN"):
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
