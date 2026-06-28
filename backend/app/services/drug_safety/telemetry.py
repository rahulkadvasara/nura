import threading
from typing import Dict, Any

class DrugSafetyTelemetry:
    """Thread-safe telemetry tracker for Drug Safety lookup and normalization operations."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.total_lookups = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.avg_latency_ms = 0.0
        self.unknown_drug_count = 0
        self.normalization_count = 0

    def record_normalization(self) -> None:
        """Increment count of normalization operations performed."""
        with self._lock:
            self.normalization_count += 1

    def record_lookup(self, cache_hit: bool, latency_ms: float, is_unknown: bool = False) -> None:
        """
        Record telemetry for a single drug lookup.
        Updates hit/miss count, unknown counts, and calculates a running average latency.
        """
        with self._lock:
            self.total_lookups += 1
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
                
            if is_unknown:
                self.unknown_drug_count += 1
                
            # Running average latency calculation
            n = self.total_lookups
            self.avg_latency_ms = (self.avg_latency_ms * (n - 1) + latency_ms) / n

    def get_statistics(self) -> Dict[str, Any]:
        """Return a snapshot dictionary of the current telemetry metrics."""
        with self._lock:
            hit_ratio = 0.0
            if self.total_lookups > 0:
                hit_ratio = self.cache_hits / self.total_lookups
                
            return {
                "total_lookups": self.total_lookups,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_ratio": hit_ratio,
                "avg_latency_ms": round(self.avg_latency_ms, 2),
                "unknown_drug_count": self.unknown_drug_count,
                "normalization_count": self.normalization_count
            }

    def reset(self) -> None:
        """Reset all tracked metrics to zero."""
        with self._lock:
            self.total_lookups = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.avg_latency_ms = 0.0
            self.unknown_drug_count = 0
            self.normalization_count = 0


# Global telemetry tracker instance
drug_safety_telemetry = DrugSafetyTelemetry()
