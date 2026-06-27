"""
Nura - Multi-Agent Orchestrator Service
"""

import time
import uuid
import logging
import threading
from typing import Optional, Dict, Any, List

from app.core.ai_config import ai_settings
from app.graph.engine import LangGraphEngine
from app.schemas.orchestrator import AIExecuteRequest, StandardResponseContract
from app.agents.base.response import AgentResponse

logger = logging.getLogger("nura.ai.multi_agent_orchestrator")


class MultiAgentTelemetryTracker:
    """Thread-safe statistics aggregator for system-wide Multi-Agent workflow execution"""

    def __init__(self):
        self._lock = threading.Lock()
        self.total_executions = 0
        self.intent_distribution = {}
        self.agent_usage = {}
        self.total_latency_ms = 0.0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.failures = 0
        self.retries = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def record_run(
        self,
        intent: str,
        agent: str,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost: float,
        success: bool
    ) -> None:
        with self._lock:
            self.total_executions += 1
            self.intent_distribution[intent] = self.intent_distribution.get(intent, 0) + 1
            self.agent_usage[agent] = self.agent_usage.get(agent, 0) + 1
            self.total_latency_ms += latency_ms
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            self.total_tokens += total_tokens
            self.total_cost += cost
            if not success:
                self.failures += 1

    def record_retry(self) -> None:
        with self._lock:
            self.retries += 1

    def record_cache(self, hit: bool) -> None:
        with self._lock:
            if hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = self.total_latency_ms / max(1, self.total_executions)
            total_cache = self.cache_hits + self.cache_misses
            cache_rate = self.cache_hits / max(1, total_cache) if total_cache > 0 else 0.0
            
            # Fetch downstream retrieval package stats if available
            retrieval_stats = {}
            try:
                from app.utils.ai import retrieval_agent_metrics
                retrieval_stats = {
                    "total_retrieval_requests": getattr(retrieval_agent_metrics, "requests", 0),
                    "total_retrieval_failures": getattr(retrieval_agent_metrics, "failures", 0),
                    "cache_hit_ratio": getattr(retrieval_agent_metrics, "cache_hit_ratio", 0.0)
                }
            except Exception:
                pass
                
            return {
                "total_executions": self.total_executions,
                "intent_distribution": dict(self.intent_distribution),
                "agent_usage": dict(self.agent_usage),
                "average_latency_ms": avg_latency,
                "total_token_usage": {
                    "prompt_tokens": self.prompt_tokens,
                    "completion_tokens": self.completion_tokens,
                    "total_tokens": self.total_tokens
                },
                "total_costs": self.total_cost,
                "failures": self.failures,
                "retries": self.retries,
                "cache_hit_rate": cache_rate,
                "retrieval_metrics": retrieval_stats
            }

    def reset(self) -> None:
        with self._lock:
            self.total_executions = 0
            self.intent_distribution.clear()
            self.agent_usage.clear()
            self.total_latency_ms = 0.0
            self.prompt_tokens = 0
            self.completion_tokens = 0
            self.total_tokens = 0
            self.total_cost = 0.0
            self.failures = 0
            self.retries = 0
            self.cache_hits = 0
            self.cache_misses = 0


# Singleton telemetry instance
_telemetry_tracker_instance = MultiAgentTelemetryTracker()


def get_multi_agent_telemetry() -> MultiAgentTelemetryTracker:
    """Retrieve multi-agent statistics tracker singleton"""
    return _telemetry_tracker_instance


class MultiAgentOrchestrator:
    """Service orchestrating the complete LangGraph Multi-Agent execution pipeline"""

    def __init__(self, engine: Optional[LangGraphEngine] = None):
        from app.graph.engine import get_graph_engine
        self.engine = engine or get_graph_engine()

    async def execute(
        self,
        request: AIExecuteRequest,
        user_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> StandardResponseContract:
        """Run standard end-to-end execution of the stateful LangGraph pipeline"""
        start_time = time.time()
        req_id = f"exec-{uuid.uuid4()}"
        
        # Build initial shared execution graph state dictionary
        state_dict = {
            "request_id": req_id,
            "session_id": request.session_id or f"sess-{uuid.uuid4()}",
            "conversation_id": request.conversation_id or f"conv-{uuid.uuid4()}",
            "patient_id": request.patient_id,
            "user_id": user_id,
            "role": role or "patient",
            "query": request.query,
            "debug_mode": request.debug_mode,
            "metadata": {
                **(request.metadata or {}),
                "initialized_at": start_time,
                "debug_mode": request.debug_mode
            }
        }

        try:
            # Execute workflow through the dynamic engine
            updated_state = await self.engine.execute_async(state_dict)
            
            # Map updated state back to standardized response contract
            metadata = updated_state.get("metadata", {})
            usage = updated_state.get("token_usage", {})
            
            # Clean up metadata properties that shouldn't leak or duplicate
            cleaned_metadata = {k: v for k, v in metadata.items() if k not in ("initialized_at", "debug_mode")}
            
            warnings = []
            # Extract safety/interaction warnings if ReminderAgent ran warned or failed
            if "reminder_analysis" in metadata:
                warnings = metadata["reminder_analysis"].get("warnings", [])
            elif "drug_interaction_analysis" in metadata:
                warnings = metadata["drug_interaction_analysis"].get("warnings", [])
                
            success = updated_state.get("error") is None
            latency_ms = (time.time() - start_time) * 1000.0
            
            # Record telemetry stats
            get_multi_agent_telemetry().record_run(
                intent=updated_state.get("detected_intent") or "UNKNOWN",
                agent=updated_state.get("selected_agent") or "UnknownAgent",
                latency_ms=latency_ms,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                cost=metadata.get("estimated_cost", 0.0),
                success=success
            )
            
            return StandardResponseContract(
                success=success,
                agent=updated_state.get("selected_agent"),
                intent=updated_state.get("detected_intent"),
                response=updated_state.get("response"),
                citations=updated_state.get("citations") or [],
                metadata=cleaned_metadata,
                usage=usage,
                execution_trace=updated_state.get("execution_trace") or [],
                execution_time=latency_ms,
                cost=metadata.get("estimated_cost", 0.0),
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Multi-Agent Orchestrator execution crashed: {str(e)}", exc_info=True)
            # Standard error fallback
            latency_ms = (time.time() - start_time) * 1000.0
            
            # Update telemetry error
            get_multi_agent_telemetry().record_run(
                intent="ERROR",
                agent="UnknownAgent",
                latency_ms=latency_ms,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                cost=0.0,
                success=False
            )
            
            return StandardResponseContract(
                success=False,
                agent=None,
                intent="ERROR",
                response=f"System execution failed: {str(e)}",
                citations=[],
                metadata={"error": str(e)},
                usage={},
                execution_trace=["__start__", "initialize_state", "error_fallback"],
                execution_time=latency_ms,
                cost=0.0,
                warnings=[f"Pipeline exception: {str(e)}"]
            )
