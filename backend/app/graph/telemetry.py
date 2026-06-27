"""
Nura - LangGraph Telemetry Tracker
Collects active performance metrics, node executions, and graph transitions telemetry.
"""

from typing import Dict, Any, Optional
from app.core.ai_config import ai_settings


class GraphTelemetryTracker:
    """In-memory metrics accumulator for monitoring graph execution workflows"""

    def __init__(self):
        self.total_executions: int = 0
        self.successful_executions: int = 0
        self.failed_executions: int = 0
        self.total_latency_ms: float = 0.0
        self.timeout_count: int = 0
        self.cancelled_count: int = 0
        self.active_executions: int = 0
        
        # Node and transition maps counters
        self.node_execution_count: Dict[str, int] = {}
        self.transition_count: Dict[str, int] = {}

    def record_start(self) -> None:
        """Record start of graph execution"""
        self.total_executions += 1
        self.active_executions += 1

    def record_success(self, latency_ms: float) -> None:
        """Record successful execution finish"""
        self.successful_executions += 1
        self.total_latency_ms += latency_ms
        if self.active_executions > 0:
            self.active_executions -= 1

    def record_failure(self, timeout: bool = False, cancelled: bool = False) -> None:
        """Record execution failure, timeout, or cancellation"""
        self.failed_executions += 1
        if timeout:
            self.timeout_count += 1
        if cancelled:
            self.cancelled_count += 1
        if self.active_executions > 0:
            self.active_executions -= 1

    def record_node_execution(self, node_name: str) -> None:
        """Increment count of node execution runs"""
        self.node_execution_count[node_name] = self.node_execution_count.get(node_name, 0) + 1

    def record_transition(self, source: str, target: str) -> None:
        """Increment count of transitions traversed"""
        t_key = f"{source}->{target}"
        self.transition_count[t_key] = self.transition_count.get(t_key, 0) + 1

    def get_metrics(self) -> Dict[str, Any]:
        """Summarize current graph performance metrics"""
        avg_latency = (
            self.total_latency_ms / self.successful_executions
            if self.successful_executions > 0
            else 0.0
        )
        
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "avg_latency": avg_latency,
            "timeout_count": self.timeout_count,
            "cancelled_count": self.cancelled_count,
            "active_executions": self.active_executions,
            "graph_version": ai_settings.GRAPH_VERSION,
            "node_execution_count": dict(self.node_execution_count),
            "transition_count": dict(self.transition_count)
        }

    def reset(self) -> None:
        """Reset internal metrics logs counters"""
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_latency_ms = 0.0
        self.timeout_count = 0
        self.cancelled_count = 0
        self.active_executions = 0
        self.node_execution_count.clear()
        self.transition_count.clear()


# Global Singleton instance
_telemetry_instance: Optional[GraphTelemetryTracker] = None


def get_graph_telemetry() -> GraphTelemetryTracker:
    """Retrieve singleton instance of GraphTelemetryTracker"""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = GraphTelemetryTracker()
    return _telemetry_instance
