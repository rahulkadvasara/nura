"""
Nura - Chat Cache Service
Provides TTL caching for chat sessions, contexts, prompt details, citations, and suggested questions.
"""
import time
import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger("nura.chat.cache")


class ChatCacheService:
    """Production-grade TTL caching layer for chat resources"""

    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        # Key: type:session_id[:additional], Value: (expiry_time, cached_value)
        self._cache: Dict[str, tuple] = {}
        self._lock = threading.Lock()
        
        # Performance metrics
        self.hits = 0
        self.misses = 0

    def _get_key(self, cache_type: str, key_suffix: str) -> str:
        return f"{cache_type}:{key_suffix}"

    def get(self, cache_type: str, key_suffix: str) -> Optional[Any]:
        key = self._get_key(cache_type, key_suffix)
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None
            expiry, val = self._cache[key]
            if time.time() > expiry:
                self._cache.pop(key, None)
                self.misses += 1
                return None
            self.hits += 1
            return val

    def set(self, cache_type: str, key_suffix: str, value: Any, ttl: Optional[int] = None) -> None:
        key = self._get_key(cache_type, key_suffix)
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        with self._lock:
            self._cache[key] = (expiry, value)

    def invalidate_by_session(self, session_id: str) -> None:
        """Removes all cache entries referencing this session_id"""
        with self._lock:
            keys_to_del = [
                k for k in self._cache.keys()
                if session_id in k
            ]
            for k in keys_to_del:
                self._cache.pop(k, None)
        logger.info(f"Invalidated chat cache entries for session: {session_id}")

    def invalidate_all(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            hit_ratio = self.hits / total if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": hit_ratio
            }


# Global singleton instance
_cache_service_instance = ChatCacheService()


def get_chat_cache_service() -> ChatCacheService:
    """Get the global ChatCacheService singleton"""
    return _cache_service_instance
