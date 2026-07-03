"""
Nura - Extended Telemetry Service
Tracks database sessions, latency performance, vector updates, streaming loops, and card usage.
"""
import time
import threading
from typing import Dict, Any

class ExtendedTelemetryTracker:
    """Aggregates real-time conversational stats in a thread-safe tracker"""

    def __init__(self):
        self._lock = threading.Lock()
        
        # Sessions
        self.total_sessions = 0
        self.active_sessions = 0
        self.archived_sessions = 0
        
        # Messages
        self.total_messages = 0
        self.user_messages = 0
        self.assistant_messages = 0
        
        # Performance
        self.total_latency = 0.0
        self.streaming_latency = 0.0
        self.retrieval_latency = 0.0
        self.prompt_latency = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # AI
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        
        # Memory
        self.conversations_evaluated = 0
        self.conversations_stored = 0
        self.patient_memory_updates = 0
        self.chat_memory_updates = 0
        
        # Streaming
        self.streams_started = 0
        self.streams_completed = 0
        self.streams_cancelled = 0
        self.streams_failed = 0
        
        # Healthcare
        self.rich_cards_generated = 0
        self.citations_generated = 0
        self.follow_ups_generated = 0

    def record_run(self, latency_ms: float, p_tokens: int, c_tokens: int, cost: float) -> None:
        with self._lock:
            self.total_sessions += 1
            self.total_messages += 2
            self.user_messages += 1
            self.assistant_messages += 1
            self.total_latency += latency_ms
            self.prompt_tokens += p_tokens
            self.completion_tokens += c_tokens
            self.total_tokens += (p_tokens + c_tokens)
            self.total_cost += cost

    def record_stream(self, event_type: str, duration_ms: float = 0.0) -> None:
        with self._lock:
            if event_type == "start":
                self.streams_started += 1
            elif event_type == "complete":
                self.streams_completed += 1
                self.streaming_latency += duration_ms
            elif event_type == "cancel":
                self.streams_cancelled += 1
            elif event_type == "fail":
                self.streams_failed += 1

    def record_memory(self, eval_sync: bool, qdrant_store: bool, patient_update: bool) -> None:
        with self._lock:
            self.conversations_evaluated += 1
            if eval_sync:
                self.conversations_stored += 1
            if qdrant_store:
                self.chat_memory_updates += 1
            if patient_update:
                self.patient_memory_updates += 1

    def record_healthcare(self, cards_count: int, citations_count: int, follow_ups_count: int) -> None:
        with self._lock:
            self.rich_cards_generated += cards_count
            self.citations_generated += citations_count
            self.follow_ups_generated += follow_ups_count

    def record_cache(self, hit: bool) -> None:
        with self._lock:
            if hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_cache = self.cache_hits + self.cache_misses
            cache_ratio = self.cache_hits / max(1, total_cache) if total_cache > 0 else 0.0
            return {
                "sessions": {
                    "total": self.total_sessions,
                    "active": self.active_sessions,
                    "archived": self.archived_sessions
                },
                "messages": {
                    "total": self.total_messages,
                    "user": self.user_messages,
                    "assistant": self.assistant_messages
                },
                "performance": {
                    "average_latency_ms": float(f"{self.total_latency / max(1, self.assistant_messages):.1f}"),
                    "average_streaming_latency_ms": float(f"{self.streaming_latency / max(1, self.streams_completed):.1f}"),
                    "average_retrieval_latency_ms": float(f"{self.retrieval_latency / max(1, self.total_sessions):.1f}"),
                    "average_prompt_latency_ms": float(f"{self.prompt_latency / max(1, self.total_sessions):.1f}"),
                    "cache_hit_ratio": float(f"{cache_ratio:.2f}")
                },
                "ai": {
                    "prompt_tokens": self.prompt_tokens,
                    "completion_tokens": self.completion_tokens,
                    "total_tokens": self.total_tokens,
                    "total_cost": float(f"{self.total_cost:.4f}")
                },
                "memory": {
                    "conversations_evaluated": self.conversations_evaluated,
                    "conversations_stored": self.conversations_stored,
                    "patient_memory_updates": self.patient_memory_updates,
                    "chat_memory_updates": self.chat_memory_updates
                },
                "streaming": {
                    "started": self.streams_started,
                    "completed": self.streams_completed,
                    "cancelled": self.streams_cancelled,
                    "failed": self.streams_failed
                },
                "healthcare": {
                    "rich_cards_generated": self.rich_cards_generated,
                    "citations_generated": self.citations_generated,
                    "follow_ups_generated": self.follow_ups_generated
                }
            }


# Global singleton instance
_extended_telemetry_instance = ExtendedTelemetryTracker()


def get_extended_telemetry() -> ExtendedTelemetryTracker:
    """Get the global ExtendedTelemetryTracker singleton"""
    return _extended_telemetry_instance
