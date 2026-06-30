import threading
from typing import Dict, Any

class DrugCacheMetricsTracker:
    """Thread-safe collector for lookup, interaction, and explanation cache statistics."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.lookup_hits = 0
        self.lookup_misses = 0
        self.interaction_hits = 0
        self.interaction_misses = 0
        self.explanation_hits = 0
        self.explanation_misses = 0
        self.invalidations = 0

    def record_hit(self, cache_type: str) -> None:
        with self._lock:
            t = cache_type.lower()
            if t == "lookup":
                self.lookup_hits += 1
            elif t == "interaction":
                self.interaction_hits += 1
            elif t == "explanation":
                self.explanation_hits += 1

    def record_miss(self, cache_type: str) -> None:
        with self._lock:
            t = cache_type.lower()
            if t == "lookup":
                self.lookup_misses += 1
            elif t == "interaction":
                self.interaction_misses += 1
            elif t == "explanation":
                self.explanation_misses += 1

    def record_invalidation(self) -> None:
        with self._lock:
            self.invalidations += 1

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            def ratio(hits, misses):
                tot = hits + misses
                return hits / tot if tot > 0 else 0.0

            return {
                "lookup_hits": self.lookup_hits,
                "lookup_misses": self.lookup_misses,
                "lookup_hit_ratio": round(ratio(self.lookup_hits, self.lookup_misses), 4),
                "interaction_hits": self.interaction_hits,
                "interaction_misses": self.interaction_misses,
                "interaction_hit_ratio": round(ratio(self.interaction_hits, self.interaction_misses), 4),
                "explanation_hits": self.explanation_hits,
                "explanation_misses": self.explanation_misses,
                "explanation_hit_ratio": round(ratio(self.explanation_hits, self.explanation_misses), 4),
                "invalidations": self.invalidations
            }

    def reset(self) -> None:
        with self._lock:
            self.lookup_hits = 0
            self.lookup_misses = 0
            self.interaction_hits = 0
            self.interaction_misses = 0
            self.explanation_hits = 0
            self.explanation_misses = 0
            self.invalidations = 0


drug_cache_metrics = DrugCacheMetricsTracker()
