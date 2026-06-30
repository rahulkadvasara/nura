import threading
from typing import Dict, Any

class DrugSafetyTelemetry:
    """Thread-safe telemetry tracker for Drug Safety lookup, normalization, interaction checking, AI explanation, and validations."""
    
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
        
        # Validation statistics
        self.validation_checks = 0
        self.validation_avg_latency_ms = 0.0
        self.reminder_validations = 0
        self.prescription_validations = 0
        self.report_validations = 0
        self.patient_memory_validations = 0
        self.other_validations = 0
        
        self.allow_decisions = 0
        self.warning_decisions = 0
        self.blocked_decisions = 0

        # AI Explanation & Cost telemetry
        self.explanation_checks = 0
        self.explanation_avg_latency_ms = 0.0
        self.fallback_executions = 0
        self.ai_cost = 0.0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

        # Core Block & Override telemetry
        self.reminder_blocks = 0
        self.prescription_overrides = 0

    def record_normalization(self) -> None:
        """Increment count of normalization operations performed."""
        with self._lock:
            self.normalization_count += 1

    def record_lookup(self, cache_hit: bool, latency_ms: float, is_unknown: bool = False) -> None:
        """Record telemetry for a single drug lookup."""
        with self._lock:
            self.total_lookups += 1
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
                
            if is_unknown:
                self.unknown_drug_count += 1
                
            n = self.total_lookups
            self.avg_latency_ms = (self.avg_latency_ms * (n - 1) + latency_ms) / n

    def record_interaction_check(self, pairs_count: int, latency_ms: float, overall_severity: str) -> None:
        """Record telemetry for an interaction check execution."""
        with self._lock:
            self.interaction_checks += 1
            self.pairs_evaluated += pairs_count
            
            n = self.interaction_checks
            self.interaction_avg_latency_ms = (self.interaction_avg_latency_ms * (n - 1) + latency_ms) / n
            
            sev_key = overall_severity.upper()
            if sev_key in self.severity_distribution:
                self.severity_distribution[sev_key] += 1
            else:
                self.severity_distribution["UNKNOWN"] += 1

    def record_validation(self, source: str, decision: str, latency_ms: float) -> None:
        """Record telemetry for a medication validation query."""
        with self._lock:
            self.validation_checks += 1
            
            n = self.validation_checks
            self.validation_avg_latency_ms = (self.validation_avg_latency_ms * (n - 1) + latency_ms) / n
            
            src = source.lower()
            if src == "reminder":
                self.reminder_validations += 1
            elif src == "prescription":
                self.prescription_validations += 1
            elif src == "report":
                self.report_validations += 1
            elif src == "patient_memory":
                self.patient_memory_validations += 1
            else:
                self.other_validations += 1
                
            dec = decision.upper()
            if dec == "ALLOW":
                self.allow_decisions += 1
            elif dec == "WARNING":
                self.warning_decisions += 1
            elif dec == "BLOCK":
                self.blocked_decisions += 1
                if src == "reminder":
                    self.reminder_blocks += 1

    def record_explanation(self, latency_ms: float, prompt_tokens: int, completion_tokens: int, cost: float, fallback_used: bool) -> None:
        """Record telemetry for an AI explanation service invocation."""
        with self._lock:
            self.explanation_checks += 1
            n = self.explanation_checks
            self.explanation_avg_latency_ms = (self.explanation_avg_latency_ms * (n - 1) + latency_ms) / n
            
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            self.total_tokens += (prompt_tokens + completion_tokens)
            self.ai_cost += cost
            if fallback_used:
                self.fallback_executions += 1

    def record_prescription_override(self) -> None:
        """Increment count of prescription overrides."""
        with self._lock:
            self.prescription_overrides += 1

    def record_reminder_block(self) -> None:
        """Increment count of reminder blocks."""
        with self._lock:
            self.reminder_blocks += 1

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
                "severity_distribution": dict(self.severity_distribution),
                
                # Validation Stats
                "validation_checks": self.validation_checks,
                "validation_avg_latency_ms": round(self.validation_avg_latency_ms, 2),
                "reminder_validations": self.reminder_validations,
                "prescription_validations": self.prescription_validations,
                "report_validations": self.report_validations,
                "patient_memory_validations": self.patient_memory_validations,
                "other_validations": self.other_validations,
                "allow_decisions": self.allow_decisions,
                "warning_decisions": self.warning_decisions,
                "blocked_decisions": self.blocked_decisions,

                # AI Explanation & Cost Stats
                "explanation_checks": self.explanation_checks,
                "explanation_avg_latency_ms": round(self.explanation_avg_latency_ms, 2),
                "fallback_executions": self.fallback_executions,
                "ai_cost": round(self.ai_cost, 6),
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,

                # Block & Override Stats
                "reminder_blocks": self.reminder_blocks,
                "prescription_overrides": self.prescription_overrides
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
            
            self.validation_checks = 0
            self.validation_avg_latency_ms = 0.0
            self.reminder_validations = 0
            self.prescription_validations = 0
            self.report_validations = 0
            self.patient_memory_validations = 0
            self.other_validations = 0
            self.allow_decisions = 0
            self.warning_decisions = 0
            self.blocked_decisions = 0

            self.explanation_checks = 0
            self.explanation_avg_latency_ms = 0.0
            self.fallback_executions = 0
            self.ai_cost = 0.0
            self.prompt_tokens = 0
            self.completion_tokens = 0
            self.total_tokens = 0
            self.reminder_blocks = 0
            self.prescription_overrides = 0


# Global telemetry tracker instance
drug_safety_telemetry = DrugSafetyTelemetry()
