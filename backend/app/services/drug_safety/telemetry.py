import threading
from typing import Dict, Any

class DrugSafetyTelemetry:
    """Thread-safe telemetry tracker for Drug Safety lookup, normalization, and interaction checking."""
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # Lookup statistics
        self.total_lookups = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.avg_latency_ms = 0.0
        self.unknown_drug_count = 0
        self.normalization_count = 0
        
        # Interaction engine statistics
        self.interaction_checks = 0
        self.pairs_evaluated = 0
        self.interaction_avg_latency_ms = 0.0
        self.severity_distribution = {
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "UNKNOWN": 0,
            "NONE": 0
        }

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

    def record_interaction_check(self, pairs_count: int, latency_ms: float, overall_severity: str) -> None:
        """
        Record telemetry for an interaction check execution.
        """
        with self._lock:
            self.interaction_checks += 1
            self.pairs_evaluated += pairs_count
            
            # Running average latency
            n = self.interaction_checks
            self.interaction_avg_latency_ms = (self.interaction_avg_latency_ms * (n - 1) + latency_ms) / n
            
            # Increment severity distribution count
            sev_key = overall_severity.upper()
            if sev_key in self.severity_distribution:
                self.severity_distribution[sev_key] += 1
            else:
                self.severity_distribution["UNKNOWN"] += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Return a snapshot dictionary of the current telemetry metrics."""
        with self._lock:
            hit_ratio = 0.0
            if self.total_lookups > 0:
                hit_ratio = self.cache_hits / self.total_lookups
                
            return {
                # Lookup Stats
                "total_lookups": self.total_lookups,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_ratio": round(hit_ratio, 4),
                "avg_latency_ms": round(self.avg_latency_ms, 2),
                "unknown_drug_count": self.unknown_drug_count,
                "normalization_count": self.normalization_count,
                
                # Interaction Stats
                "interaction_checks": self.interaction_checks,
                "pairs_evaluated": self.pairs_evaluated,
                "interaction_avg_latency_ms": round(self.interaction_avg_latency_ms, 2),
                "severity_distribution": dict(self.severity_distribution)
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
            
            self.interaction_checks = 0
            self.pairs_evaluated = 0
            self.interaction_avg_latency_ms = 0.0
            self.severity_distribution = {
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
                "UNKNOWN": 0,
                "NONE": 0
            }


# Global telemetry tracker instance
drug_safety_telemetry = DrugSafetyTelemetry()
