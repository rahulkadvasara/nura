import time
import json
import hashlib
import logging
import threading
from typing import Dict, Any, List, Optional, Set, Tuple

from app.services.drug_cache.cache_metrics import drug_cache_metrics

logger = logging.getLogger("nura.services.drug_cache")

class DrugCacheService:
    """
    Centralized TTL caching for Drug Safety platform.
    Manages lookup cache (24h), interaction cache (15m), and AI explanation cache (6h).
    Supports patient-level cache key registration and invalidation.
    """

    LOOKUP_TTL = 24 * 3600       # 24 hours
    INTERACTION_TTL = 15 * 60    # 15 minutes
    EXPLANATION_TTL = 6 * 3600   # 6 hours

    def __init__(self):
        self._lock = threading.Lock()
        
        # Cache dictionaries mapping Key -> (expires_at, value)
        self._lookup_cache: Dict[str, Tuple[float, Any]] = {}
        self._interaction_cache: Dict[str, Tuple[float, Any]] = {}
        self._explanation_cache: Dict[str, Tuple[float, Any]] = {}

        # Patient key association to enable targeted invalidation: patient_id -> Set of (cache_type, key)
        self._patient_keys: Dict[str, Set[Tuple[str, str]]] = {}

    # --- Hash Helper Functions ---
    @staticmethod
    def get_medication_list_hash(medications: List[str]) -> str:
        """Calculate deterministic MD5 hash for a list of medication names."""
        cleaned = sorted([m.strip().upper() for m in medications if m and m.strip()])
        serialized = json.dumps(cleaned)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def get_interaction_hash(interactions: List[Dict[str, Any]]) -> str:
        """Calculate deterministic MD5 hash for detected interactions list."""
        standardized = []
        for inter in interactions:
            if hasattr(inter, "model_dump"):
                item = inter.model_dump()
            elif isinstance(inter, dict):
                item = inter
            else:
                item = getattr(inter, "__dict__", {})

            standardized.append({
                "drug_a_normalized": item.get("drug_a_normalized", "").upper(),
                "drug_b_normalized": item.get("drug_b_normalized", "").upper(),
                "severity": item.get("severity", "").upper(),
                "description": item.get("description", "")
            })
        
        # Sort to ensure order independence
        standardized.sort(key=lambda x: (x["drug_a_normalized"], x["drug_b_normalized"]))
        serialized = json.dumps(standardized)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    # --- Patient Key Registration ---
    def register_patient_key(self, patient_id: str, cache_type: str, key: str) -> None:
        """Associate a cache key with a patient ID for targeted eviction."""
        if not patient_id:
            return
        with self._lock:
            if patient_id not in self._patient_keys:
                self._patient_keys[patient_id] = set()
            self._patient_keys[patient_id].add((cache_type, key))

    # --- Invalidation API ---
    def invalidate_patient(self, patient_id: str) -> None:
        """Invalidate all cached interactions and explanations associated with a patient."""
        if not patient_id:
            return
        logger.info(f"Invalidating cache for patient {patient_id}")
        
        with self._lock:
            keys_to_evict = self._patient_keys.pop(patient_id, None)
            if keys_to_evict:
                drug_cache_metrics.record_invalidation()
                for cache_type, key in keys_to_evict:
                    if cache_type == "interaction":
                        self._interaction_cache.pop(key, None)
                    elif cache_type == "explanation":
                        self._explanation_cache.pop(key, None)

    def invalidate_database_cache(self) -> None:
        """Clear lookup cache (e.g., when drug database changes)."""
        logger.info("Invalidating drug database lookup cache")
        with self._lock:
            self._lookup_cache.clear()
            drug_cache_metrics.record_invalidation()

    # --- Cache Lookup & Ingestion ---
    def get_lookup(self, normalized_drug_name: str) -> Optional[Any]:
        with self._lock:
            key = normalized_drug_name.strip().upper()
            if key in self._lookup_cache:
                expires_at, val = self._lookup_cache[key]
                if time.time() < expires_at:
                    drug_cache_metrics.record_hit("lookup")
                    return val
                else:
                    self._lookup_cache.pop(key, None)
            
            drug_cache_metrics.record_miss("lookup")
            return None

    def set_lookup(self, normalized_drug_name: str, value: Any) -> None:
        with self._lock:
            key = normalized_drug_name.strip().upper()
            self._lookup_cache[key] = (time.time() + self.LOOKUP_TTL, value)

    def get_interaction(self, medications: List[str], patient_id: Optional[str] = None) -> Optional[Any]:
        key = self.get_medication_list_hash(medications)
        if patient_id:
            self.register_patient_key(patient_id, "interaction", key)
            
        with self._lock:
            if key in self._interaction_cache:
                expires_at, val = self._interaction_cache[key]
                if time.time() < expires_at:
                    drug_cache_metrics.record_hit("interaction")
                    return val
                else:
                    self._interaction_cache.pop(key, None)
            
            drug_cache_metrics.record_miss("interaction")
            return None

    def set_interaction(self, medications: List[str], value: Any, patient_id: Optional[str] = None) -> None:
        key = self.get_medication_list_hash(medications)
        if patient_id:
            self.register_patient_key(patient_id, "interaction", key)
            
        with self._lock:
            self._interaction_cache[key] = (time.time() + self.INTERACTION_TTL, value)

    def get_explanation(self, interactions: List[Dict[str, Any]], patient_id: Optional[str] = None) -> Optional[Any]:
        key = self.get_interaction_hash(interactions)
        if patient_id:
            self.register_patient_key(patient_id, "explanation", key)
            
        with self._lock:
            if key in self._explanation_cache:
                expires_at, val = self._explanation_cache[key]
                if time.time() < expires_at:
                    drug_cache_metrics.record_hit("explanation")
                    return val
                else:
                    self._explanation_cache.pop(key, None)
            
            drug_cache_metrics.record_miss("explanation")
            return None

    def set_explanation(self, interactions: List[Dict[str, Any]], value: Any, patient_id: Optional[str] = None) -> None:
        key = self.get_interaction_hash(interactions)
        if patient_id:
            self.register_patient_key(patient_id, "explanation", key)
            
        with self._lock:
            self._explanation_cache[key] = (time.time() + self.EXPLANATION_TTL, value)

    def clear(self) -> None:
        """Flush all cache directories and reset performance counters."""
        with self._lock:
            self._lookup_cache.clear()
            self._interaction_cache.clear()
            self._explanation_cache.clear()
            self._patient_keys.clear()
        drug_cache_metrics.reset()

    def get_stats(self) -> Dict[str, Any]:
        """Retrieve telemetry diagnostics for sizing and ratio trends."""
        with self._lock:
            sizes = {
                "lookup_cache_size": len(self._lookup_cache),
                "interaction_cache_size": len(self._interaction_cache),
                "explanation_cache_size": len(self._explanation_cache),
                "tracked_patients_count": len(self._patient_keys)
            }
        metrics = drug_cache_metrics.get_metrics()
        return {**sizes, **metrics}


# Global Singleton Reference Cache
_drug_cache_service_instance: Optional[DrugCacheService] = None

def get_drug_cache_service() -> DrugCacheService:
    global _drug_cache_service_instance
    if _drug_cache_service_instance is None:
        _drug_cache_service_instance = DrugCacheService()
    return _drug_cache_service_instance
