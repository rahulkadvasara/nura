import threading
from typing import Dict, Any, Optional

class DrugSafetyAITelemetry:
    """Thread-safe telemetry tracker for Drug AI Explanation generation metrics"""

    def __init__(self):
        self._lock = threading.Lock()
        self.explanation_requests = 0
        self.successful_generations = 0
        self.fallback_executions = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.estimated_cost = 0.0
        self.total_latency_ms = 0.0
        self.model_usage: Dict[str, int] = {}

    def record_request(self) -> None:
        with self._lock:
            self.explanation_requests += 1

    def record_success(self, model: str, prompt_tokens: int, completion_tokens: int, latency_ms: float) -> None:
        with self._lock:
            self.successful_generations += 1
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            # Simple pricing heuristic for Groq (e.g. Llama-3 70b pricing: $0.15/1M input, $0.60/1M output)
            cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)
            self.estimated_cost += cost
            self.total_latency_ms += latency_ms
            self.model_usage[model] = self.model_usage.get(model, 0) + 1

    def record_fallback(self) -> None:
        with self._lock:
            self.fallback_executions += 1

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = 0.0
            if self.successful_generations > 0:
                avg_latency = self.total_latency_ms / self.successful_generations
            
            return {
                "explanation_requests": self.explanation_requests,
                "successful_generations": self.successful_generations,
                "fallback_executions": self.fallback_executions,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.prompt_tokens + self.completion_tokens,
                "estimated_cost": round(self.estimated_cost, 6),
                "avg_latency_ms": round(avg_latency, 2),
                "model_usage": dict(self.model_usage)
            }

    def reset(self) -> None:
        with self._lock:
            self.explanation_requests = 0
            self.successful_generations = 0
            self.fallback_executions = 0
            self.prompt_tokens = 0
            self.completion_tokens = 0
            self.estimated_cost = 0.0
            self.total_latency_ms = 0.0
            self.model_usage.clear()


_telemetry_instance: Optional[DrugSafetyAITelemetry] = None

def get_drug_ai_telemetry() -> DrugSafetyAITelemetry:
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = DrugSafetyAITelemetry()
    return _telemetry_instance
