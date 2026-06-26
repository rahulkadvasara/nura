"""
Nura - RAG Monitoring Service
Aggregates in-memory metrics, cache hit ratios, service latencies, and token costs.
"""

from typing import Dict, Any, Optional
from app.utils.ai import (
    embedding_metrics,
    retrieval_metrics,
    context_assembly_metrics,
    retrieval_agent_metrics,
    rag_cache_metrics,
    orchestrator_metrics
)
from app.core.ai_config import ai_settings


class RAGMonitoringService:
    """Consolidates performance, cost, cache, and health telemetry statistics"""

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Compile complete statistics report across RAG and LLM components"""
        cache_stats = rag_cache_metrics.get_metrics()
        embed_stats = embedding_metrics.get_metrics()
        search_stats = retrieval_metrics.get_metrics()
        assembly_stats = context_assembly_metrics.get_metrics()
        agent_stats = retrieval_agent_metrics.get_metrics()
        orchestrator_stats = orchestrator_metrics.get_metrics()

        # Calculate combined metrics
        success_rate = search_stats.get("searches_executed", 0) - search_stats.get("failed_searches", 0)
        total_searches = search_stats.get("searches_executed", 0)
        overall_success_ratio = success_rate / total_searches if total_searches > 0 else 1.0

        return {
            "health_status": "healthy",
            "caches": cache_stats,
            "embeddings": embed_stats,
            "retrieval": search_stats,
            "assembly": assembly_stats,
            "agent": agent_stats,
            "orchestrator": orchestrator_stats,
            "overall": {
                "success_rate": overall_success_ratio,
                "total_queries": agent_stats.get("requests", 0),
                "avg_query_latency_ms": agent_stats.get("avg_latency_ms", 0.0),
                "estimated_llm_cost_usd": orchestrator_stats.get("total_cost", 0.0)
            }
        }

    def reset_all_metrics(self) -> None:
        """Reset all in-memory metrics trackers"""
        rag_cache_metrics.reset()
        embedding_metrics.reset()
        retrieval_metrics.reset()
        context_assembly_metrics.reset()
        retrieval_agent_metrics.reset()
        orchestrator_metrics.reset()


# Singleton instance helper
_monitoring_service_instance: Optional[RAGMonitoringService] = None


def get_rag_monitoring_service() -> RAGMonitoringService:
    """Retrieve singleton instance of RAGMonitoringService"""
    global _monitoring_service_instance
    if _monitoring_service_instance is None:
        _monitoring_service_instance = RAGMonitoringService()
    return _monitoring_service_instance
