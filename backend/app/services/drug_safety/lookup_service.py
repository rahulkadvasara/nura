import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.drug_safety.normalizer import DrugNormalizer
from app.services.drug_safety.telemetry import drug_safety_telemetry
from app.services.drug_cache.drug_cache_service import get_drug_cache_service
from app.utils.circuit_breaker import get_circuit_breaker

logger = logging.getLogger("nura.services.drug_lookup")

class DrugLookupService:
    """Service to resolve drug queries against drug_master collection with TTL cache and telemetry tracking."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.master_col = database.drug_master
        self.cache_service = get_drug_cache_service()
        self.mongodb_breaker = get_circuit_breaker("mongodb", failure_threshold=5, recovery_timeout=30.0)

    async def lookup(self, drug_name: str) -> Dict[str, Any]:
        """
        Lookup a drug name. Normalizes the name, checks cache, and resolves via MongoDB drug_master.
        """
        start_time = time.perf_counter()
        
        # 1. Normalize
        normalized_name = DrugNormalizer.normalize(drug_name)
        drug_safety_telemetry.record_normalization()
        
        if not normalized_name:
            latency = (time.perf_counter() - start_time) * 1000.0
            drug_safety_telemetry.record_lookup(cache_hit=False, latency_ms=latency, is_unknown=True)
            return {
                "exists": False,
                "matched_drug": None,
                "normalized_name": "",
                "lookup_source": "none",
                "confidence": 0.0,
                "latency_ms": round(latency, 2)
            }
            
        # 2. Check Cache
        cached_res = self.cache_service.get_lookup(normalized_name)
        if cached_res is not None:
            latency = (time.perf_counter() - start_time) * 1000.0
            drug_safety_telemetry.record_lookup(cache_hit=True, latency_ms=latency, is_unknown=not cached_res["exists"])
            return {
                "exists": cached_res["exists"],
                "matched_drug": cached_res["matched_drug"],
                "normalized_name": normalized_name,
                "lookup_source": "cache",
                "confidence": 1.0 if cached_res["exists"] else 0.0,
                "latency_ms": round(latency, 2)
            }

        # 3. Query Database with Circuit Breaker
        async def db_query():
            doc = await self.master_col.find_one({"normalized_name": normalized_name})
            confidence = 1.0
            if not doc:
                doc = await self.master_col.find_one({"aliases": normalized_name})
                confidence = 0.9 if doc else 0.0
            return doc, confidence

        try:
            doc, confidence = await self.mongodb_breaker.execute_async(db_query)
        except Exception as e:
            logger.error(f"MongoDB lookup failed: {e}. Falling back to empty cache results.")
            doc, confidence = None, 0.0

        # Serialize MongoDB document
        matched_drug = None
        if doc:
            matched_drug = {
                "id": str(doc["_id"]),
                "drug_name": doc["drug_name"],
                "normalized_name": doc["normalized_name"],
                "aliases": doc.get("aliases", []),
                "source_dataset": doc.get("source_dataset", "ddinter")
            }
            
        # 4. Update Cache
        cache_entry = {
            "exists": matched_drug is not None,
            "matched_drug": matched_drug
        }
        self.cache_service.set_lookup(normalized_name, cache_entry)
            
        # 5. Record Telemetry
        latency = (time.perf_counter() - start_time) * 1000.0
        is_unknown = (matched_drug is None)
        drug_safety_telemetry.record_lookup(cache_hit=False, latency_ms=latency, is_unknown=is_unknown)
        
        return {
            "exists": matched_drug is not None,
            "matched_drug": matched_drug,
            "normalized_name": normalized_name,
            "lookup_source": "database",
            "confidence": confidence,
            "latency_ms": round(latency, 2)
        }

    async def bulk_lookup(self, drug_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Perform lookup for a list of drug names. Returns a dictionary mapping original_name -> lookup result.
        """
        results = {}
        tasks = [self.lookup(name) for name in drug_names]
        lookup_results = await asyncio.gather(*tasks)
        
        for name, res in zip(drug_names, lookup_results):
            results[name] = res
            
        return results

    async def exists(self, drug_name: str) -> bool:
        """Helper to quickly check if a drug exists in the database/cache."""
        res = await self.lookup(drug_name)
        return res["exists"]

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Return statistics on cache sizes and hit ratios."""
        return self.cache_service.get_stats()
            
    async def clear_cache(self) -> None:
        """Clear all entries in the cache."""
        self.cache_service.clear()
