"""
Nura - Operations Telemetry Registry
Thread-safe singleton to track operational execution metrics
"""

import threading
from typing import Dict, Any


class OperationsTelemetryRegistry:
    """Telemetry registry recording execution performance of ReminderAgent and AppointmentAgent"""

    def __init__(self):
        self._lock = threading.Lock()
        self._stats: Dict[str, Dict[str, Any]] = {
            "ReminderAgent": {
                "execution_count": 0,
                "failures": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
                "average_latency_ms": 0.0,
                "downstream_service_calls": 0,
                "total_latency_ms": 0.0,
            },
            "AppointmentAgent": {
                "execution_count": 0,
                "failures": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
                "average_latency_ms": 0.0,
                "downstream_service_calls": 0,
                "total_latency_ms": 0.0,
            }
        }

    def record_execution(
        self,
        agent_name: str,
        success: bool,
        latency_ms: float,
        tokens: int,
        cost: float,
        service_calls: int = 1
    ) -> None:
        """Update metrics thread-safely for the given agent"""
        if agent_name not in self._stats:
            return

        with self._lock:
            stats = self._stats[agent_name]
            stats["execution_count"] += 1
            if not success:
                stats["failures"] += 1
            stats["total_latency_ms"] += latency_ms
            stats["average_latency_ms"] = stats["total_latency_ms"] / stats["execution_count"]
            stats["total_tokens"] += tokens
            stats["estimated_cost"] += cost
            stats["downstream_service_calls"] += service_calls

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of the metrics snapshot"""
        with self._lock:
            return {name: dict(metrics) for name, metrics in self._stats.items()}

    def reset(self) -> None:
        """Reset all counters to zero"""
        with self._lock:
            for agent in self._stats:
                for k in self._stats[agent]:
                    if isinstance(self._stats[agent][k], float):
                        self._stats[agent][k] = 0.0
                    else:
                        self._stats[agent][k] = 0


# Global singleton
_telemetry_instance = OperationsTelemetryRegistry()


def get_operations_telemetry() -> OperationsTelemetryRegistry:
    """Retrieve the operational telemetry singleton"""
    return _telemetry_instance
