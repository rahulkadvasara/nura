import time
import pytest
from app.services.chat.cache_service import ChatCacheService


def test_cache_set_get():
    cache = ChatCacheService(default_ttl=5)
    cache.set("session", "sess123", "value123")
    assert cache.get("session", "sess123") == "value123"
    assert cache.get("session", "other") is None


def test_cache_ttl():
    cache = ChatCacheService(default_ttl=1)
    cache.set("session", "sess123", "value123", ttl=1)
    assert cache.get("session", "sess123") == "value123"
    time.sleep(1.1)
    assert cache.get("session", "sess123") is None


def test_cache_invalidation():
    cache = ChatCacheService()
    cache.set("prompt", "sess123:hello", "response1")
    cache.set("prompt", "sess456:hello", "response2")
    cache.set("citations", "sess123:chunks", "citations1")

    assert cache.get("prompt", "sess123:hello") == "response1"
    assert cache.get("prompt", "sess456:hello") == "response2"

    cache.invalidate_by_session("sess123")
    assert cache.get("prompt", "sess123:hello") is None
    assert cache.get("citations", "sess123:chunks") is None
    assert cache.get("prompt", "sess456:hello") == "response2"


def test_cache_stats():
    cache = ChatCacheService()
    cache.invalidate_all()
    cache.set("session", "sess1", "val1")
    
    assert cache.get("session", "sess1") == "val1"  # Hit
    assert cache.get("session", "sess2") is None      # Miss
    
    stats = cache.get_statistics()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_ratio"] == 0.5
