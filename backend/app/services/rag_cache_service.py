"""
Nura - RAG Cache Service
Centralized in-memory TTL caching for queries, embeddings, retrieval results, and assembled contexts.
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.core.ai_config import ai_settings, AISettings
from app.utils.ai import rag_cache_metrics

logger = logging.getLogger("nura.ai.cache")


def serialize_key_params(
    query: str,
    collections: List[str],
    filters: Optional[Dict[str, Any]],
    top_k: Optional[int] = None,
    score_threshold: Optional[float] = None,
    token_budget: Optional[int] = None,
    patient_id: Optional[str] = None
) -> str:
    """Helper to convert query, collections, filters, and other params into a stable string key"""
    normalized_query = query.strip().lower()
    sorted_collections = sorted(collections) if collections else []
    
    # Stable serialization of filters dictionary
    serialized_filters = ""
    if filters:
        try:
            serialized_filters = json.dumps(filters, sort_keys=True)
        except Exception:
            serialized_filters = str(filters)
            
    key_dict = {
        "q": normalized_query,
        "c": sorted_collections,
        "f": serialized_filters,
    }
    if top_k is not None:
        key_dict["tk"] = top_k
    if score_threshold is not None:
        key_dict["st"] = score_threshold
    if token_budget is not None:
        key_dict["tb"] = token_budget
    if patient_id is not None:
        key_dict["pid"] = patient_id
        
    return json.dumps(key_dict, sort_keys=True)


class RAGCacheService:
    """Production-grade RAG Caching Service containing separate TTL buffers for each RAG stage"""

    def __init__(self, settings: AISettings = ai_settings):
        self.settings = settings
        
        # Caches store tuple of (timestamp, value)
        self._query_cache: Dict[str, Tuple[float, Any]] = {}
        self._embedding_cache: Dict[str, Tuple[float, List[float]]] = {}
        self._retrieval_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
        self._context_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def prune_expired(self) -> None:
        """Helper to clear expired keys across all caches to free up memory"""
        now = time.time()
        
        # 1. Query Cache
        for k in list(self._query_cache.keys()):
            ts, _ = self._query_cache[k]
            if now - ts > self.settings.QUERY_CACHE_TTL:
                del self._query_cache[k]
                
        # 2. Embedding Cache
        for k in list(self._embedding_cache.keys()):
            ts, _ = self._embedding_cache[k]
            if now - ts > self.settings.EMBEDDING_CACHE_TTL:
                del self._embedding_cache[k]
                
        # 3. Retrieval Cache
        for k in list(self._retrieval_cache.keys()):
            ts, _ = self._retrieval_cache[k]
            if now - ts > self.settings.RETRIEVAL_CACHE_TTL:
                del self._retrieval_cache[k]
                
        # 4. Context Cache
        for k in list(self._context_cache.keys()):
            ts, _ = self._context_cache[k]
            if now - ts > self.settings.CONTEXT_CACHE_TTL:
                del self._context_cache[k]

    # --- Query Cache ---
    def get_query(self, query: str) -> Optional[Tuple[str, Dict[str, float]]]:
        """Retrieve cached intent classification results for a query"""
        normalized = query.strip().lower()
        if normalized in self._query_cache:
            ts, val = self._query_cache[normalized]
            if time.time() - ts <= self.settings.QUERY_CACHE_TTL:
                rag_cache_metrics.record_hit("query")
                return val
            else:
                del self._query_cache[normalized]
                
        rag_cache_metrics.record_miss("query")
        return None

    def set_query(self, query: str, intent: str, intent_scores: Dict[str, float]) -> None:
        """Cache intent classification results for a query"""
        normalized = query.strip().lower()
        self._query_cache[normalized] = (time.time(), (intent, intent_scores))

    # --- Embedding Cache ---
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieve cached vector embedding for a given text chunk"""
        text_hash = text.strip()  # Direct string matching as key
        if text_hash in self._embedding_cache:
            ts, val = self._embedding_cache[text_hash]
            if time.time() - ts <= self.settings.EMBEDDING_CACHE_TTL:
                rag_cache_metrics.record_hit("embedding")
                return val
            else:
                del self._embedding_cache[text_hash]
                
        rag_cache_metrics.record_miss("embedding")
        return None

    def set_embedding(self, text: str, vector: List[float]) -> None:
        """Cache vector embedding for a given text chunk"""
        text_hash = text.strip()
        self._embedding_cache[text_hash] = (time.time(), vector)

    # --- Retrieval Cache ---
    def get_retrieval(
        self,
        query: str,
        collections: List[str],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached multi-collection retrieval search results"""
        key = serialize_key_params(
            query=query,
            collections=collections,
            filters=filters,
            top_k=top_k,
            score_threshold=score_threshold
        )
        if key in self._retrieval_cache:
            ts, val = self._retrieval_cache[key]
            if time.time() - ts <= self.settings.RETRIEVAL_CACHE_TTL:
                rag_cache_metrics.record_hit("retrieval")
                return val
            else:
                del self._retrieval_cache[key]
                
        rag_cache_metrics.record_miss("retrieval")
        return None

    def set_retrieval(
        self,
        query: str,
        collections: List[str],
        filters: Optional[Dict[str, Any]],
        top_k: int,
        score_threshold: Optional[float],
        results: List[Dict[str, Any]]
    ) -> None:
        """Cache multi-collection retrieval search results"""
        key = serialize_key_params(
            query=query,
            collections=collections,
            filters=filters,
            top_k=top_k,
            score_threshold=score_threshold
        )
        self._retrieval_cache[key] = (time.time(), results)

    # --- Context Cache ---
    def get_context(
        self,
        patient_id: Optional[str],
        query: str,
        token_budget: int,
        collections: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached context assembly prompt results"""
        key = serialize_key_params(
            query=query,
            collections=collections,
            filters=filters,
            token_budget=token_budget,
            patient_id=patient_id
        )
        if key in self._context_cache:
            ts, val = self._context_cache[key]
            if time.time() - ts <= self.settings.CONTEXT_CACHE_TTL:
                rag_cache_metrics.record_hit("context")
                return val
            else:
                del self._context_cache[key]
                
        rag_cache_metrics.record_miss("context")
        return None

    def set_context(
        self,
        patient_id: Optional[str],
        query: str,
        token_budget: int,
        collections: List[str],
        filters: Optional[Dict[str, Any]],
        assembled: Dict[str, Any]
    ) -> None:
        """Cache context assembly prompt results"""
        key = serialize_key_params(
            query=query,
            collections=collections,
            filters=filters,
            token_budget=token_budget,
            patient_id=patient_id
        )
        self._context_cache[key] = (time.time(), assembled)

    def clear(self) -> None:
        """Clear all RAG cache storages"""
        self._query_cache.clear()
        self._embedding_cache.clear()
        self._retrieval_cache.clear()
        self._context_cache.clear()


# Global Singleton Reference Cache
_rag_cache_service_instance: Optional[RAGCacheService] = None


def get_rag_cache_service() -> RAGCacheService:
    """Retrieve singleton instance of RAGCacheService"""
    global _rag_cache_service_instance
    if _rag_cache_service_instance is None:
        _rag_cache_service_instance = RAGCacheService(settings=ai_settings)
    return _rag_cache_service_instance
