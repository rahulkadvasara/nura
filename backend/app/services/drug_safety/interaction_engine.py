import time
from typing import List, Dict, Any, Set, Tuple
from itertools import combinations
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.drug_safety.lookup_service import DrugLookupService
from app.services.drug_safety.severity_classifier import SeverityClassifier
from app.services.drug_safety.recommendation_builder import RecommendationBuilder
from app.services.drug_safety.telemetry import drug_safety_telemetry
from app.services.drug_safety.models import DrugCheckResponse, InteractionPairDetail


class DrugInteractionEngine:
    """Deterministic drug-drug interaction validation engine using MongoDB."""

    def __init__(self, database: AsyncIOMotorDatabase, lookup_service: DrugLookupService):
        self.db = database
        self.interactions_col = database.drug_interactions
        self.lookup_service = lookup_service

    async def check_interactions(self, medications: List[str]) -> DrugCheckResponse:
        """
        Check for drug-drug interactions in a list of raw medication names.
        Deduplicates, normalizes, generates pairs, and queries MongoDB.
        """
        start_time = time.perf_counter()
        
        # 1. Resolve and normalize each medication
        resolved_meds = []
        normalized_meds = []
        normalized_to_original: Dict[str, str] = {}
        
        for med in medications:
            if not med or not med.strip():
                continue
            
            # Resolve against drug_master via lookup_service
            lookup_res = await self.lookup_service.lookup(med)
            
            if lookup_res["exists"] and lookup_res["matched_drug"]:
                norm_name = lookup_res["matched_drug"]["normalized_name"]
                normalized_to_original[norm_name] = med
                
                # Prevent duplicate resolved names
                if norm_name not in normalized_meds:
                    normalized_meds.append(norm_name)
                    resolved_meds.append(med)
            else:
                # Track lookup failures in telemetry (already done in lookup_service.lookup)
                # We can also add it to normalized_to_original as itself to track warning if needed
                pass

        # 2. Generate unique combination pairs of size 2
        pairs = list(combinations(normalized_meds, 2))
        
        detected_interactions: List[InteractionPairDetail] = []
        severities = []
        
        # 3. Query drug_interactions in MongoDB if there are pairs
        if pairs:
            query_conditions = []
            for norm_a, norm_b in pairs:
                query_conditions.append({"drug_a_normalized": norm_a, "drug_b_normalized": norm_b})
                query_conditions.append({"drug_a_normalized": norm_b, "drug_b_normalized": norm_a})
                
            cursor = self.interactions_col.find({"$or": query_conditions})
            docs = await cursor.to_list(length=1000)
            
            # De-duplicate bidirectional matches in database results
            seen_interaction_keys = set()
            
            for doc in docs:
                norm_a = doc["drug_a_normalized"]
                norm_b = doc["drug_b_normalized"]
                
                # Standard key for de-duplicating A-B and B-A
                key = tuple(sorted([norm_a, norm_b]))
                if key in seen_interaction_keys:
                    continue
                seen_interaction_keys.add(key)
                
                severity = doc.get("severity", "UNKNOWN")
                severities.append(severity)
                
                detail = InteractionPairDetail(
                    drug_a=normalized_to_original.get(norm_a, doc.get("drug_a", norm_a)),
                    drug_a_normalized=norm_a,
                    drug_b=normalized_to_original.get(norm_b, doc.get("drug_b", norm_b)),
                    drug_b_normalized=norm_b,
                    severity=severity,
                    description=doc.get("interaction_description", "")
                )
                detected_interactions.append(detail)

        # 4. Classify overall severity & build recommendations
        overall_severity = SeverityClassifier.classify(severities)
        recommendations = RecommendationBuilder.build(overall_severity)
        
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        # 5. Record telemetry
        drug_safety_telemetry.record_interaction_check(
            pairs_count=len(pairs),
            latency_ms=latency_ms,
            overall_severity=overall_severity
        )
        
        # Fetch current statistics snapshot for the response
        stats = drug_safety_telemetry.get_statistics()
        
        return DrugCheckResponse(
            medications=medications,
            normalized_medications=normalized_meds,
            detected_interactions=detected_interactions,
            severity=overall_severity,
            recommendations=recommendations,
            statistics=stats,
            latency_ms=round(latency_ms, 2)
        )
