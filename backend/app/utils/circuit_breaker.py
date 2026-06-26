"""
Nura - Circuit Breaker Utility
Protects external services (Groq, Qdrant, Embedding Engine) from cascading failures.
"""

import time
import asyncio
import logging
from typing import Callable, Any, Optional, Dict

logger = logging.getLogger("nura.utils.circuit_breaker")


class CircuitBreakerOpenException(Exception):
    """Exception raised when a call is attempted while the circuit breaker is OPEN"""
    pass


class CircuitBreaker:
    """
    Generic State Machine for Circuit Breaker Pattern.
    States: CLOSED, OPEN, HALF_OPEN
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        fallback_func: Optional[Callable] = None
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fallback_func = fallback_func
        
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.last_state_change = time.time()
        self.last_failure_time = 0.0

    def _to_state(self, new_state: str) -> None:
        """Transitions state and records timestamp"""
        if self.state != new_state:
            logger.warning(f"[CircuitBreaker-{self.name}] State transition: {self.state} -> {new_state}")
            self.state = new_state
            self.last_state_change = time.time()

    def before_call(self) -> None:
        """Checks if calls are allowed. Transitions from OPEN to HALF_OPEN if timeout has elapsed."""
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change > self.recovery_timeout:
                self._to_state("HALF_OPEN")
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN. Cooldown active for {self.recovery_timeout - (now - self.last_state_change):.1f}s."
                )

    def record_success(self) -> None:
        """Records a successful operation. Resets state to CLOSED if it was HALF_OPEN."""
        if self.state == "HALF_OPEN":
            logger.info(f"[CircuitBreaker-{self.name}] Service recovered. Resetting to CLOSED.")
            self._to_state("CLOSED")
            self.failure_count = 0
        elif self.state == "CLOSED":
            self.failure_count = 0

    def record_failure(self, error: Exception) -> None:
        """Records an operation failure. Opens circuit if failure threshold is reached."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.error(f"[CircuitBreaker-{self.name}] Failure recorded ({self.failure_count}/{self.failure_threshold}): {error}")
        
        if self.state in ("CLOSED", "HALF_OPEN"):
            if self.failure_count >= self.failure_threshold or self.state == "HALF_OPEN":
                self._to_state("OPEN")

    def execute_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Executes a synchronous function wrapped with circuit breaker protection"""
        try:
            self.before_call()
        except CircuitBreakerOpenException as e:
            if self.fallback_func:
                logger.info(f"[CircuitBreaker-{self.name}] Circuit is OPEN. Triggering fallback.")
                return self.fallback_func(*args, **kwargs)
            raise e

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            if self.fallback_func:
                logger.info(f"[CircuitBreaker-{self.name}] Call failed. Triggering fallback.")
                return self.fallback_func(*args, **kwargs)
            raise e

    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Executes an asynchronous function wrapped with circuit breaker protection"""
        try:
            self.before_call()
        except CircuitBreakerOpenException as e:
            if self.fallback_func:
                logger.info(f"[CircuitBreaker-{self.name}] Circuit is OPEN. Triggering fallback.")
                if asyncio.iscoroutinefunction(self.fallback_func):
                    return await self.fallback_func(*args, **kwargs)
                return self.fallback_func(*args, **kwargs)
            raise e

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            if self.fallback_func:
                logger.info(f"[CircuitBreaker-{self.name}] Call failed. Triggering fallback.")
                if asyncio.iscoroutinefunction(self.fallback_func):
                    return await self.fallback_func(*args, **kwargs)
                return self.fallback_func(*args, **kwargs)
            raise e


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    fallback_func: Optional[Callable] = None
) -> CircuitBreaker:
    """Retrieve or create a singleton named CircuitBreaker"""
    global _circuit_breakers
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            fallback_func=fallback_func
        )
    return _circuit_breakers[name]
