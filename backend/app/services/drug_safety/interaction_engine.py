import time
import copy
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from itertools import combinations
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.drug_safety.lookup_service import DrugLookupService
from app.services.drug_safety.severity_classifier import SeverityClassifier
from app.services.drug_safety.recommendation_builder import RecommendationBuilder
from app.services.drug_safety.telemetry import drug_safety_telemetry
from app.services.drug_safety.models import DrugCheckResponse, InteractionPairDetail
from app.services.drug_cache.drug_cache_service import get_drug_cache_service
from app.utils.circuit_breaker import get_circuit_breaker

logger = logging.getLogger("nura.services.drug_interaction_engine")

class DrugInteractionEngine:
    """Deterministic drug-drug interaction validation engine using MongoDB."""

    def __init__(self, database: AsyncIOMotorDatabase, lookup_service: DrugLookupService):
        self.db = database
        self.interactions_col = database.drug_interactions
        self.lookup_service = lookup_service
        self.cache_service = get_drug_cache_service()
        self.mongodb_breaker = get_circuit_breaker("mongodb", failure_threshold=5, recovery_timeout=30.0)

    async def check_interactions(self, medications: List[str], patient_id: Optional[str] = None) -> DrugCheckResponse:
        """
        Check for drug-drug interactions in a list of raw medication names.
        Deduplicates, normalizes, generates pairs, and queries MongoDB.
        """
        start_time = time.perf_counter()
        
        # 1. Resolve and check cache first
        cached_val = self.cache_service.get_interaction(medications, patient_id)
        if cached_val is not None:
            res = copy.deepcopy(cached_val)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            res.latency_ms = round(latency_ms, 2)
            res.statistics = drug_safety_telemetry.get_statistics()
            
            drug_safety_telemetry.record_interaction_check(
                pairs_count=len(res.detected_interactions),
                latency_ms=latency_ms,
                overall_severity=res.severity
            )
            return res
        
        # 2. Bulk Lookup to resolve and normalize each medication
        resolved_meds = []
        normalized_meds = []
        normalized_to_original: Dict[str, str] = {}
        
        # Filter empty strings
        clean_meds = [m for m in medications if m and m.strip()]
        if clean_meds:
            lookup_results = await self.lookup_service.bulk_lookup(clean_meds)
            for med in clean_meds:
                lookup_res = lookup_results.get(med)
                if lookup_res and lookup_res["exists"] and lookup_res["matched_drug"]:
                    norm_name = lookup_res["matched_drug"]["normalized_name"]
                    normalized_to_original[norm_name] = med
                    
                    if norm_name not in normalized_meds:
                        normalized_meds.append(norm_name)
                        resolved_meds.append(med)

        # 3. Generate unique combination pairs of size 2
        pairs = list(combinations(normalized_meds, 2))
        detected_interactions: List[InteractionPairDetail] = []
        severities = []
        
        # 4. Query drug_interactions in MongoDB if there are pairs
        if pairs:
            query_conditions = []
            for norm_a, norm_b in pairs:
                query_conditions.append({"drug_a_normalized": norm_a, "drug_b_normalized": norm_b})
                query_conditions.append({"drug_a_normalized": norm_b, "drug_b_normalized": norm_a})
                
            async def run_db_query():
                cursor = self.interactions_col.find({"$or": query_conditions})
                return await cursor.to_list(length=1000)

            try:
                docs = await self.mongodb_breaker.execute_async(run_db_query)
            except Exception as e:
                logger.error(f"MongoDB drug_interactions check failed: {e}. Returning empty list.")
                docs = []
            
            # De-duplicate bidirectional matches in database results
            seen_interaction_keys = set()
            
            for doc in docs:
                norm_a = doc["drug_a_normalized"]
                norm_b = doc["drug_b_normalized"]
                
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

        # 5. Classify overall severity & build recommendations
        overall_severity = SeverityClassifier.classify(severities)
        recommendations = RecommendationBuilder.build(overall_severity)
        
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        # 6. Record telemetry
        drug_safety_telemetry.record_interaction_check(
            pairs_count=len(pairs),
            latency_ms=latency_ms,
            overall_severity=overall_severity
        )
        
        stats = drug_safety_telemetry.get_statistics()
        
        response = DrugCheckResponse(
            medications=medications,
            normalized_medications=normalized_meds,
            detected_interactions=detected_interactions,
            severity=overall_severity,
            recommendations=recommendations,
            statistics=stats,
            latency_ms=round(latency_ms, 2)
        )
        
        # 7. Cache the result
        self.cache_service.set_interaction(medications, response, patient_id)
        
        return response
