"""
Nura - Retrieval Agent
Concrete Retrieval Agent implementing intent-aware multi-collection vector search and context assembly.
"""
import time
from typing import Any, Optional, Dict, List
from app.agents.base.retrieval_agent import RetrievalAgent as BaseRetrievalAgent
from app.agents.base.context import AgentContext
from app.agents.base.response import AgentResponse
from app.services.intent_detection_service import IntentDetectionService
from app.services.retrieval_service import RetrievalService
from app.services.context_assembly_service import ContextAssemblyService
from app.core.ai_config import ai_settings
from app.utils.ai import retrieval_agent_metrics

# Simple in-memory cache class for RetrievalAgent results
class RetrievalCache:
    """In-memory TTL cache for Retrieval Agent output packages"""

    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        # Key: (patient_id, query, intent), Value: (timestamp, package_data)
        self.cache: Dict[tuple, tuple] = {}

    def get(self, patient_id: Optional[str], query: str, intent: str) -> Optional[dict]:
        key = (patient_id, query.strip().lower(), intent)
        if key not in self.cache:
            return None
        timestamp, data = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key] # Expired
            return None
        return data

    def set(self, patient_id: Optional[str], query: str, intent: str, data: dict) -> None:
        key = (patient_id, query.strip().lower(), intent)
        self.cache[key] = (time.time(), data)

    def clear(self) -> None:
        self.cache.clear()

# Global cache instance
retrieval_cache = RetrievalCache(ttl=ai_settings.RETRIEVAL_CACHE_TTL)

class RetrievalAgent(BaseRetrievalAgent):
    """Production-grade Retrieval Agent coordinating intent routing and context assembly"""

    def __init__(
        self,
        intent_detector: IntentDetectionService,
        retrieval_service: RetrievalService,
        context_assembly: ContextAssemblyService,
        settings=ai_settings
    ):
        super().__init__(name="Retrieval Agent", settings=settings)
        self.intent_detector = intent_detector
        self.retrieval_service = retrieval_service
        self.context_assembly = context_assembly

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute intent classification, query collection routing, Qdrant search,
        context assembly, citation mapping, caching, and timing metrics collection.
        """
        query = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        # Override intent from context metadata if provided, otherwise detect
        forced_intent = context.metadata.get("intent") if context else None
        
        # 1. Intent Detection
        start_total = time.perf_counter()
        if forced_intent:
            intent = forced_intent
            intent_scores = {intent: 10}
        else:
            intent, intent_scores = self.intent_detector.detect_intent_with_scores(query)

        # 2. Collection Routing
        # Mapping of intents to standard Qdrant collections
        intent_collections = {
            "medical_question": ["medical_knowledge", "patient_reports"],
            "report_analysis": ["patient_reports"],
            "drug_question": ["drug_knowledge", "patient_reports"],
            "doctor_recommendation": ["doctor_knowledge"],
            "conversation_recall": ["chat_memory"],
            "general_health": ["medical_knowledge"],
            "unknown": ["medical_knowledge"]
        }
        
        collections = intent_collections.get(intent, ["medical_knowledge"])

        # 3. Check Cache
        bypass_cache = context.metadata.get("bypass_cache", False) if context else False
        cached_result = None if bypass_cache else retrieval_cache.get(patient_id, query, intent)
        if cached_result is not None:
            # Record cache hit metrics
            retrieval_agent_metrics.record_execution(
                intent=intent,
                collections=collections,
                cache_hit=True,
                retrieval_latency_ms=0.0,
                ranking_latency_ms=0.0,
                context_latency_ms=0.0,
                total_latency_ms=(time.perf_counter() - start_total) * 1000.0,
                success=True
            )
            # Mark cached status
            cached_result["cache_status"] = "hit"
            return cached_result

        # 4. Multi-Collection Retrieval (Cache Miss)
        start_retrieval = time.perf_counter()
        
        # Pull metadata filters if supplied
        filters = context.metadata.get("filters") if context else None
        top_k = context.metadata.get("top_k", 5) if context else 5
        score_threshold = context.metadata.get("score_threshold") if context else None
        
        retrieval_raw = await self.retrieval_service.retrieve_multiple(
            query=query,
            collections=collections,
            filters=filters,
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        retrieval_latency = (time.perf_counter() - start_retrieval) * 1000.0
        
        # Deduplication and ranking latency estimation (part of retrieval service execution)
        ranking_latency = retrieval_latency * 0.15 # Heuristic separation

        # 5. Context Assembly
        start_context = time.perf_counter()
        
        token_budget = context.metadata.get("token_budget", 4000) if context else 4000
        
        # Build prioritized token-budgeted prompt context block
        assembly_result = await self.context_assembly.assemble(
            query=query,
            patient_id=patient_id,
            token_budget=token_budget,
            collections=collections,
            filters=filters
        )
        
        context_latency = (time.perf_counter() - start_context) * 1000.0
        total_latency = (time.perf_counter() - start_total) * 1000.0

        # Construct flat lookup scores mapping for point matches
        scores_map = {match["id"]: match["score"] for match in retrieval_raw.get("results", [])}

        # Build output RetrievalPackage
        package_data = {
            "intent": intent,
            "collections_used": collections,
            "retrieved_chunks": retrieval_raw.get("results", []),
            "context": assembly_result.get("context", ""),
            "citations": assembly_result.get("citations", {}),
            "metadata": {
                "intent_scores": intent_scores,
                "token_budget": token_budget,
                "compression_ratio": assembly_result.get("compression_ratio", 0.0),
                "estimated_tokens": assembly_result.get("estimated_tokens", 0)
            },
            "latency": {
                "retrieval": retrieval_latency,
                "ranking": ranking_latency,
                "context": context_latency,
                "total": total_latency
            },
            "scores": scores_map,
            "cache_status": "miss"
        }

        # Save to cache
        retrieval_cache.set(patient_id, query, intent, package_data)

        # Record metrics
        retrieval_agent_metrics.record_execution(
            intent=intent,
            collections=collections,
            cache_hit=False,
            retrieval_latency_ms=retrieval_latency,
            ranking_latency_ms=ranking_latency,
            context_latency_ms=context_latency,
            total_latency_ms=total_latency,
            success=True
        )

        return package_data
