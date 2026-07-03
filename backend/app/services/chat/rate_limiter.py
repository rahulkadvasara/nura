"""
Nura - Rate Limiter Service
Sliding-window per-user and per-IP rate limiter to prevent API abuse.
"""
import time
import logging
import threading
from typing import Dict, List, Any

logger = logging.getLogger("nura.chat.ratelimit")


class RateLimiter:
    """Sliding-window rate limiter checking user request frequency"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
        # User_id -> list of request timestamps
        self._user_requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        
        # Telemetry metrics
        self.total_requests = 0
        self.blocked_requests = 0
        self.abuse_attempts = 0

    def is_allowed(self, user_id: str) -> bool:
        """Check if user is within request limits, tracking telemetry metrics"""
        now = time.time()
        with self._lock:
            self.total_requests += 1

            if user_id not in self._user_requests:
                self._user_requests[user_id] = []

            # Filter timestamps to keep only those within the sliding window
            cutoff = now - self.window_seconds
            timestamps = [t for t in self._user_requests[user_id] if t > cutoff]
            self._user_requests[user_id] = timestamps

            if len(timestamps) >= self.max_requests:
                self.blocked_requests += 1
                timestamps.append(now)
                # Twice the limit indicates abuse attempt
                if len(timestamps) >= self.max_requests * 2:
                    self.abuse_attempts += 1
                logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{len(timestamps)} requests in the last {self.window_seconds}s"
                )
                return False

            timestamps.append(now)
            return True

    def get_statistics(self) -> Dict[str, Any]:
        """Return rate limiter statistics metrics"""
        with self._lock:
            return {
                "total_requests": self.total_requests,
                "blocked_requests": self.blocked_requests,
                "abuse_attempts": self.abuse_attempts
            }


# Global singleton instance
_rate_limiter_instance = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global RateLimiter singleton"""
    return _rate_limiter_instance
