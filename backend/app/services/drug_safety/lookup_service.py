import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.drug_safety.normalizer import DrugNormalizer
from app.services.drug_safety.telemetry import drug_safety_telemetry


class DrugLookupService:
    """Service to resolve drug queries against drug_master collection with TTL cache and telemetry tracking."""

    def __init__(self, database: AsyncIOMotorDatabase, ttl_seconds: int = 600):
        self.db = database
        self.master_col = database.drug_master
        self.ttl = ttl_seconds
        
        # In-memory cache structure: normalized_name -> (lookup_dict_or_none, expiration_timestamp)
        self._cache: Dict[str, Tuple[Optional[Dict[str, Any]], float]] = {}
        self._cache_lock = asyncio.Lock()
        
        # Local cache metrics
        self.cache_hits_count = 0
        self.cache_misses_count = 0

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
            
        now = time.time()
        
        # 2. Check Cache
        async with self._cache_lock:
            if normalized_name in self._cache:
                cached_val, expires_at = self._cache[normalized_name]
                if now < expires_at:
                    self.cache_hits_count += 1
                    latency = (time.perf_counter() - start_time) * 1000.0
                    drug_safety_telemetry.record_lookup(cache_hit=True, latency_ms=latency, is_unknown=(cached_val is None))
                    
                    if cached_val is None:
                        return {
                            "exists": False,
                            "matched_drug": None,
                            "normalized_name": normalized_name,
                            "lookup_source": "cache",
                            "confidence": 0.0,
                            "latency_ms": round(latency, 2)
                        }
                    
                    # Compute confidence based on exact match vs alias match
                    confidence = 1.0 if cached_val["normalized_name"] == normalized_name else 0.9
                    return {
                        "exists": True,
                        "matched_drug": cached_val,
                        "normalized_name": normalized_name,
                        "lookup_source": "cache",
                        "confidence": confidence,
                        "latency_ms": round(latency, 2)
                    }
                else:
                    # Expired, clean it up
                    del self._cache[normalized_name]
            
            self.cache_misses_count += 1

        # 3. Query Database
        db_start = time.perf_counter()
        
        # Exact match check
        doc = await self.master_col.find_one({"normalized_name": normalized_name})
        confidence = 1.0
        
        if not doc:
            # Alias match check
            doc = await self.master_col.find_one({"aliases": normalized_name})
            confidence = 0.9 if doc else 0.0
            
        latency = (time.perf_counter() - start_time) * 1000.0
        
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
        async with self._cache_lock:
            self._cache[normalized_name] = (matched_drug, now + self.ttl)
            
        # 5. Record Telemetry
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
        # Simple parallel gather, since lookup utilizes locks and DB connection pooling
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
        async with self._cache_lock:
            total = self.cache_hits_count + self.cache_misses_count
            ratio = self.cache_hits_count / total if total > 0 else 0.0
            return {
                "cache_size": len(self._cache),
                "hits": self.cache_hits_count,
                "misses": self.cache_misses_count,
                "hit_ratio": round(ratio, 4)
            }
            
    async def clear_cache(self) -> None:
        """Clear all entries in the cache."""
        async with self._cache_lock:
            self._cache.clear()
            self.cache_hits_count = 0
            self.cache_misses_count = 0
