"""
Nura - Clinical Report AI Telemetry
"""

import threading
from typing import Dict, Any


class ReportAiTelemetry:
    """Thread-safe telemetry registry for clinical report AI summarization pipeline runs"""

    def __init__(self):
        self._lock = threading.Lock()
        self.total_generations = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens_consumed = 0
        self.accumulated_cost = 0.0
        self.accumulated_latency_ms = 0.0
        self.model_usage = {}

    def record_generation(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        cost: float,
        success: bool
    ) -> None:
        with self._lock:
            self.total_generations += 1
            if success:
                self.successful_runs += 1
                self.total_prompt_tokens += prompt_tokens
                self.total_completion_tokens += completion_tokens
                self.total_tokens_consumed += (prompt_tokens + completion_tokens)
                self.accumulated_cost += cost
                self.accumulated_latency_ms += latency_ms
                self.model_usage[model] = self.model_usage.get(model, 0) + 1
            else:
                self.failed_runs += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = 0.0
            if self.successful_runs > 0:
                avg_latency = self.accumulated_latency_ms / self.successful_runs

            return {
                "total_generations": self.total_generations,
                "successful_runs": self.successful_runs,
                "failed_runs": self.failed_runs,
                "total_prompt_tokens": self.total_prompt_tokens,
                "total_completion_tokens": self.total_completion_tokens,
                "total_tokens_consumed": self.total_tokens_consumed,
                "accumulated_cost": round(self.accumulated_cost, 6),
                "average_latency_ms": round(avg_latency, 2),
                "model_usage_metrics": dict(self.model_usage)
            }

    def reset(self) -> None:
        with self._lock:
            self.total_generations = 0
            self.successful_runs = 0
            self.failed_runs = 0
            self.total_prompt_tokens = 0
            self.total_completion_tokens = 0
            self.total_tokens_consumed = 0
            self.accumulated_cost = 0.0
            self.accumulated_latency_ms = 0.0
            self.model_usage.clear()


# Singleton reference
_telemetry_instance = ReportAiTelemetry()


def get_report_ai_telemetry() -> ReportAiTelemetry:
    """Retrieve singleton report AI telemetry instance"""
    return _telemetry_instance
