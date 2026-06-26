"""
Nura - AI Utilities
Utility classes for tracking token usage, estimating api costs, and collecting in-memory metrics
"""

import time
from typing import Dict, Any


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate estimated cost in USD based on Groq pricing model per 1M tokens.
    
    Pricing:
    - llama-3.3-70b-versatile: Input $0.59/1M, Output $0.79/1M
    - llama-3.1-8b-instant: Input $0.05/1M, Output $0.08/1M
    - mixtral-8x7b-32768: Input $0.24/1M, Output $0.24/1M
    """
    pricing = {
        "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
        "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
        "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
    }
    
    # Locate appropriate model key from prefix/substring match, default to llama-3.3-70b-versatile
    selected_key = "llama-3.3-70b-versatile"
    for key in pricing:
        if key in model:
            selected_key = key
            break
            
    rates = pricing[selected_key]
    input_cost = (prompt_tokens / 1_000_000.0) * rates["input"]
    output_cost = (completion_tokens / 1_000_000.0) * rates["output"]
    return input_cost + output_cost


class TokenTracker:
    """Utility for tracking token usage, latency, and costs for AI requests"""
    
    def __init__(self, model: str):
        self.model: str = model
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        
    def start(self) -> None:
        """Start tracking time"""
        self.start_time = time.time()
        
    def stop(self) -> float:
        """Stop tracking time and return latency in milliseconds"""
        self.end_time = time.time()
        return self.latency_ms
        
    @property
    def latency_ms(self) -> float:
        """Calculate elapsed time in milliseconds"""
        if self.start_time == 0.0:
            return 0.0
        end = self.end_time if self.end_time > 0.0 else time.time()
        return (end - self.start_time) * 1000.0
        
    @property
    def total_tokens(self) -> int:
        """Total tokens utilized"""
        return self.prompt_tokens + self.completion_tokens
        
    @property
    def cost(self) -> float:
        """Estimated cost in USD"""
        return estimate_cost(self.model, self.prompt_tokens, self.completion_tokens)


class AIMetricsTracker:
    """In-memory metrics tracker for monitoring AI infrastructure performance"""
    
    def __init__(self):
        self._requests: int = 0
        self._failures: int = 0
        self._total_latency_ms: float = 0.0
        self._total_tokens: int = 0
        
    def record_success(self, latency_ms: float, tokens: int) -> None:
        """Record a successful AI request"""
        self._requests += 1
        self._total_latency_ms += latency_ms
        self._total_tokens += tokens
        
    def record_failure(self) -> None:
        """Record a failed AI request"""
        self._requests += 1
        self._failures += 1
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get summarized AI performance metrics"""
        successful_requests = self._requests - self._failures
        avg_latency = (self._total_latency_ms / successful_requests) if successful_requests > 0 else 0.0
        avg_tokens = (self._total_tokens / successful_requests) if successful_requests > 0 else 0.0
        
        return {
            "requests": self._requests,
            "failures": self._failures,
            "avg_latency": avg_latency,
            "avg_tokens": avg_tokens,
            "success_rate": (successful_requests / self._requests) if self._requests > 0 else 1.0
        }
        
    def reset(self) -> None:
        """Reset in-memory counters"""
        self._requests = 0
        self._failures = 0
        self._total_latency_ms = 0.0
        self._total_tokens = 0


# Global metrics tracker instance
ai_metrics = AIMetricsTracker()


class EmbeddingMetricsTracker:
    """In-memory metrics tracker for monitoring AI embedding performance"""
    
    def __init__(self):
        self.embeddings_generated: int = 0
        self.total_latency_ms: float = 0.0
        self.failed_embeddings: int = 0
        self.batch_sizes: list = []
        self.duplicate_chunks_skipped: int = 0
        
    def record_success(self, count: int, latency_ms: float, batch_size: int) -> None:
        """Record successful embedding generations"""
        self.embeddings_generated += count
        self.total_latency_ms += latency_ms
        if batch_size > 1:
            self.batch_sizes.append(batch_size)
            
    def record_failure(self, count: int = 1) -> None:
        """Record failed embedding requests"""
        self.failed_embeddings += count
        
    def record_duplicate(self, count: int = 1) -> None:
        """Record duplicate chunks skipped"""
        self.duplicate_chunks_skipped += count
        
    def get_metrics(self) -> Dict[str, Any]:
        """Summarize current embedding performance metrics"""
        avg_latency = (self.total_latency_ms / self.embeddings_generated) if self.embeddings_generated > 0 else 0.0
        avg_batch_size = (sum(self.batch_sizes) / len(self.batch_sizes)) if self.batch_sizes else 0.0
        return {
            "embeddings_generated": self.embeddings_generated,
            "avg_latency_ms": avg_latency,
            "failed_embeddings": self.failed_embeddings,
            "avg_batch_size": avg_batch_size,
            "duplicate_chunks_skipped": self.duplicate_chunks_skipped
        }
        
    def reset(self) -> None:
        """Reset internal metric counters"""
        self.embeddings_generated = 0
        self.total_latency_ms = 0.0
        self.failed_embeddings = 0
        self.batch_sizes = []
        self.duplicate_chunks_skipped = 0


# Global embedding metrics tracker instance
embedding_metrics = EmbeddingMetricsTracker()


class AgentMetricsTracker:
    """In-memory metrics tracker for monitoring AI agents performance"""
    
    def __init__(self):
        self.executions: int = 0
        self.failures: int = 0
        self.total_latency_ms: float = 0.0
        self.retries: int = 0
        self.timeouts: int = 0
        self.streaming_usages: int = 0
        self.total_tokens: int = 0
        self.model_usage: dict = {}
        
    def record_execution(
        self,
        latency_ms: float,
        success: bool,
        tokens: int = 0,
        retries: int = 0,
        timeout: bool = False,
        streaming: bool = False,
        model: str = None
    ) -> None:
        """Record telemetry of an agent execution"""
        self.executions += 1
        self.total_latency_ms += latency_ms
        if not success:
            self.failures += 1
        if timeout:
            self.timeouts += 1
        self.retries += retries
        if streaming:
            self.streaming_usages += 1
        self.total_tokens += tokens
        if model:
            self.model_usage[model] = self.model_usage.get(model, 0) + 1
            
    def get_metrics(self) -> dict:
        """Summarize current agent performance metrics"""
        successful = self.executions - self.failures
        avg_latency = (self.total_latency_ms / self.executions) if self.executions > 0 else 0.0
        avg_tokens = (self.total_tokens / successful) if successful > 0 else 0.0
        return {
            "executions": self.executions,
            "failures": self.failures,
            "avg_latency_ms": avg_latency,
            "retries": self.retries,
            "timeouts": self.timeouts,
            "streaming_usages": self.streaming_usages,
            "avg_tokens": avg_tokens,
            "model_usage": self.model_usage
        }
        
    def reset(self) -> None:
        """Reset internal metric counters"""
        self.executions = 0
        self.failures = 0
        self.total_latency_ms = 0.0
        self.retries = 0
        self.timeouts = 0
        self.streaming_usages = 0
        self.total_tokens = 0
        self.model_usage = {}


# Global agent metrics tracker instance
agent_metrics = AgentMetricsTracker()


class OrchestratorMetricsTracker:
    """In-memory metrics tracker for monitoring AI Orchestrator performance"""

    def __init__(self):
        self.requests: int = 0
        self.failures: int = 0
        self.total_llm_latency_ms: float = 0.0
        self.total_embedding_latency_ms: float = 0.0
        self.total_context_latency_ms: float = 0.0
        self.total_latency_ms: float = 0.0
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.model_usage: dict = {}

    def record_orchestration(
        self,
        llm_latency_ms: float,
        embedding_latency_ms: float,
        context_latency_ms: float,
        total_latency_ms: float,
        success: bool,
        tokens: int = 0,
        cost: float = 0.0,
        model: str = None
    ) -> None:
        """Record telemetry metrics from an orchestrator execution lifecycle"""
        self.requests += 1
        self.total_latency_ms += total_latency_ms
        self.total_llm_latency_ms += llm_latency_ms
        self.total_embedding_latency_ms += embedding_latency_ms
        self.total_context_latency_ms += context_latency_ms
        
        if not success:
            self.failures += 1
        self.total_tokens += tokens
        self.total_cost += cost
        if model:
            self.model_usage[model] = self.model_usage.get(model, 0) + 1

    def get_metrics(self) -> dict:
        """Summarize current orchestrator performance metrics"""
        successful = self.requests - self.failures
        avg_latency = (self.total_latency_ms / self.requests) if self.requests > 0 else 0.0
        avg_llm_latency = (self.total_llm_latency_ms / self.requests) if self.requests > 0 else 0.0
        avg_embedding_latency = (self.total_embedding_latency_ms / self.requests) if self.requests > 0 else 0.0
        avg_context_latency = (self.total_context_latency_ms / self.requests) if self.requests > 0 else 0.0
        avg_tokens = (self.total_tokens / successful) if successful > 0 else 0.0
        
        return {
            "requests": self.requests,
            "failures": self.failures,
            "avg_latency_ms": avg_latency,
            "avg_llm_latency_ms": avg_llm_latency,
            "avg_embedding_latency_ms": avg_embedding_latency,
            "avg_context_latency_ms": avg_context_latency,
            "avg_tokens": avg_tokens,
            "total_cost": self.total_cost,
            "model_usage": self.model_usage,
            "success_rate": ((self.requests - self.failures) / self.requests) if self.requests > 0 else 1.0
        }

    def reset(self) -> None:
        """Reset internal metrics counters"""
        self.requests = 0
        self.failures = 0
        self.total_llm_latency_ms = 0.0
        self.total_embedding_latency_ms = 0.0
        self.total_context_latency_ms = 0.0
        self.total_latency_ms = 0.0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.model_usage = {}


# Global orchestrator metrics tracker instance
orchestrator_metrics = OrchestratorMetricsTracker()


class IndexingMetricsTracker:
    """In-memory metrics tracker for monitoring AI document indexing pipeline performance"""

    def __init__(self):
        self.indexed_documents: int = 0
        self.indexed_chunks: int = 0
        self.duplicate_documents_skipped: int = 0
        self.total_chunk_size_chars: int = 0
        self.total_chunks_processed_for_size: int = 0

    def record_indexing(self, chunks_count: int, total_chars: int) -> None:
        """Record successful document indexing event"""
        self.indexed_documents += 1
        self.indexed_chunks += chunks_count
        self.total_chunk_size_chars += total_chars
        self.total_chunks_processed_for_size += chunks_count

    def record_duplicate_skip(self) -> None:
        """Record a skipped duplicate document event"""
        self.duplicate_documents_skipped += 1

    def get_metrics(self) -> dict:
        """Summarize current indexing performance metrics"""
        avg_chunk_size = (
            self.total_chunk_size_chars / self.total_chunks_processed_for_size
            if self.total_chunks_processed_for_size > 0
            else 0.0
        )
        return {
            "indexed_documents": self.indexed_documents,
            "indexed_chunks": self.indexed_chunks,
            "duplicate_documents_skipped": self.duplicate_documents_skipped,
            "avg_chunk_size": avg_chunk_size
        }

    def reset(self) -> None:
        """Reset internal metrics counters"""
        self.indexed_documents = 0
        self.indexed_chunks = 0
        self.duplicate_documents_skipped = 0
        self.total_chunk_size_chars = 0
        self.total_chunks_processed_for_size = 0


# Global indexing metrics tracker instance
indexing_metrics = IndexingMetricsTracker()



