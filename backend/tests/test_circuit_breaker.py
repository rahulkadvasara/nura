"""
Nura - Unit tests for CircuitBreaker
"""
import pytest
import asyncio
import time
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException

def test_circuit_breaker_transitions():
    cb = CircuitBreaker("test-service", failure_threshold=2, recovery_timeout=0.1)

    # Starts in CLOSED state
    assert cb.state == "CLOSED"

    # Single failure shouldn't open
    cb.record_failure(ValueError("err"))
    assert cb.state == "CLOSED"

    # Second failure should open
    cb.record_failure(ValueError("err"))
    assert cb.state == "OPEN"

    # Calling before_call should raise open exception
    with pytest.raises(CircuitBreakerOpenException):
        cb.before_call()

    # Wait for recovery timeout
    time.sleep(0.12)
    
    # Check that it moves to HALF_OPEN
    cb.before_call()
    assert cb.state == "HALF_OPEN"

    # Successful call should close
    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.failure_count == 0

def test_circuit_breaker_execute_sync_fallback():
    fallback_mock = MagicMock(return_value="fallback_data")
    cb = CircuitBreaker("test-sync", failure_threshold=1, recovery_timeout=1.0, fallback_func=fallback_mock)

    def failing_func():
        raise ValueError("failing")

    # CLOSED state execution failing triggers fallback
    res = cb.execute_sync(failing_func)
    assert res == "fallback_data"
    assert cb.state == "OPEN"
    fallback_mock.assert_called_once()

    # OPEN state execution triggers fallback directly without invoking failing function
    fallback_mock.reset_mock()
    res2 = cb.execute_sync(failing_func)
    assert res2 == "fallback_data"
    fallback_mock.assert_called_once()

@pytest.mark.asyncio
async def test_circuit_breaker_execute_async_fallback():
    async def fallback_async():
        return "async_fallback"
    
    cb = CircuitBreaker("test-async", failure_threshold=1, recovery_timeout=1.0, fallback_func=fallback_async)

    async def failing_async():
        raise ValueError("failing async")

    res = await cb.execute_async(failing_async)
    assert res == "async_fallback"
    assert cb.state == "OPEN"

from unittest.mock import MagicMock
