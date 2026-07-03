import time
import pytest
from app.services.chat.rate_limiter import RateLimiter


def test_rate_limiter_allowed():
    limiter = RateLimiter(max_requests=3, window_seconds=2)
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is False


def test_rate_limiter_window_expiry():
    limiter = RateLimiter(max_requests=2, window_seconds=1)
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is False
    
    time.sleep(1.1)
    assert limiter.is_allowed("user1") is True


def test_rate_limiter_abuse_attempt():
    limiter = RateLimiter(max_requests=2, window_seconds=2)
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is False # Blocked 1
    assert limiter.is_allowed("user1") is False # Blocked 2
    assert limiter.is_allowed("user1") is False # Blocked 3, triggers abuse
    
    stats = limiter.get_statistics()
    assert stats["blocked_requests"] == 3
    assert stats["abuse_attempts"] >= 1
