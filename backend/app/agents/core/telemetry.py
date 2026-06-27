"""
Nura - Core Agents Telemetry Tracker
Collects, aggregates, and reports performance and execution tokens telemetry for core agents.
"""

import threading
from typing import Dict, Any


class CoreAgentsTelemetryTracker:
    """Cumulative in-memory statistics tracker for individual AI agents executions"""

    def __init__(self):
        self._lock = threading.Lock()
        self._stats: Dict[str, Dict[str, Any]] = {
            "MedicalKnowledgeAgent": self._default_stats(),
            "SymptomAgent": self._default_stats(),
            "MemoryAgent": self._default_stats()
        }

    def _default_stats(self) -> Dict[str, Any]:
        return {
            "execution_count": 0,
            "total_latency_ms": 0.0,
            "average_latency_ms": 0.0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "failures": 0,
            "retrieval_latency_ms": 0.0,
            "groq_latency_ms": 0.0
        }

    def record_run(
        self,
        agent_name: str,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        estimated_cost: float,
        success: bool = True,
        retrieval_latency_ms: float = 0.0,
        groq_latency_ms: float = 0.0
    ) -> None:
        """Accumulate execution metrics variables for the designated agent"""
        with self._lock:
            if agent_name not in self._stats:
                self._stats[agent_name] = self._default_stats()
            
            stats = self._stats[agent_name]
            stats["execution_count"] += 1
            
            if not success:
                stats["failures"] += 1
                return

            stats["total_latency_ms"] += latency_ms
            stats["average_latency_ms"] = stats["total_latency_ms"] / max(1, stats["execution_count"] - stats["failures"])
            stats["prompt_tokens"] += prompt_tokens
            stats["completion_tokens"] += completion_tokens
            stats["total_tokens"] += total_tokens
            stats["estimated_cost"] += estimated_cost
            stats["retrieval_latency_ms"] += retrieval_latency_ms
            stats["groq_latency_ms"] += groq_latency_ms

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of the gathered statistics summary"""
        with self._lock:
            return {k: dict(v) for k, v in self._stats.items()}

    def reset(self) -> None:
        """Reset all aggregated counters"""
        with self._lock:
            for k in self._stats:
                self._stats[k] = self._default_stats()


# Global singleton instance
_tracker_instance = CoreAgentsTelemetryTracker()


def get_core_agents_telemetry() -> CoreAgentsTelemetryTracker:
    """Retrieve singleton tracker instance"""
    return _tracker_instance
