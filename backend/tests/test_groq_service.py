"""
Nura - Groq Service Unit Tests
Verifies configuration validation, successful prompt generation, health checks, and custom exception mapping.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import groq

from app.core.ai_config import AISettings
from app.core.exceptions import (
    AIConfigurationError,
    AIConnectionError,
    AITimeoutError,
    AIRateLimitError,
    AIResponseError
)
from app.services.groq_service import GroqService, handle_groq_exceptions


def test_groq_service_missing_api_key():
    """Verify that a missing API key throws an AIConfigurationError"""
    settings = AISettings(GROQ_API_KEY="", GROQ_MODEL="llama-3.3-70b-versatile")
    with pytest.raises(AIConfigurationError):
        GroqService(settings=settings)


@pytest.mark.asyncio
@patch("app.services.groq_service.AsyncGroq")
async def test_groq_service_generate_success(mock_async_groq):
    """Verify successful response generation under normal conditions"""
    mock_client = MagicMock()
    mock_async_groq.return_value = mock_client
    
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Test execution response content"
    mock_choice.finish_reason = "stop"
    mock_response.choices = [mock_choice]
    mock_response.usage = MagicMock(prompt_tokens=15, completion_tokens=25, total_tokens=40)
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    settings = AISettings(GROQ_API_KEY="valid_test_key", GROQ_MODEL="llama-3.3-70b-versatile")
    service = GroqService(settings=settings)
    
    response = await service.generate(prompt="What is healthy eating?")
    assert response.choices[0].message.content == "Test execution response content"
    assert response.usage.total_tokens == 40
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.groq_service.AsyncGroq")
async def test_groq_service_health_check_healthy(mock_async_groq):
    """Verify health check reports healthy when the API call succeeds"""
    mock_client = MagicMock()
    mock_async_groq.return_value = mock_client
    mock_client.chat.completions.create = AsyncMock()
    
    settings = AISettings(GROQ_API_KEY="valid_test_key", GROQ_MODEL="llama-3.3-70b-versatile")
    service = GroqService(settings=settings)
    
    health = await service.health_check()
    assert health["reachable"] is True
    assert health["status"] == "healthy"
    assert "latency_ms" in health


@pytest.mark.asyncio
@patch("app.services.groq_service.AsyncGroq")
async def test_groq_service_health_check_unhealthy(mock_async_groq):
    """Verify health check reports unhealthy when a connection failure occurs"""
    mock_client = MagicMock()
    mock_async_groq.return_value = mock_client
    mock_client.chat.completions.create = AsyncMock(side_effect=groq.APIConnectionError(request=MagicMock()))
    
    settings = AISettings(GROQ_API_KEY="valid_test_key", GROQ_MODEL="llama-3.3-70b-versatile")
    service = GroqService(settings=settings)
    
    health = await service.health_check()
    assert health["reachable"] is False
    assert health["status"] == "unhealthy"
    assert "error" in health


@pytest.mark.asyncio
async def test_exception_mapping():
    """Verify that official Groq client SDK errors are mapped to our internal exception classes"""
    with pytest.raises(AITimeoutError):
        async with handle_groq_exceptions():
            raise groq.APITimeoutError(request=MagicMock())
            
    with pytest.raises(AIConnectionError):
        async with handle_groq_exceptions():
            raise groq.APIConnectionError(request=MagicMock())
            
    with pytest.raises(AIRateLimitError):
        async with handle_groq_exceptions():
            raise groq.RateLimitError(message="rate limit hit", response=MagicMock(status_code=429, headers={}), body=None)
            
    with pytest.raises(AIResponseError):
        async with handle_groq_exceptions():
            raise groq.APIStatusError(message="bad request", response=MagicMock(status_code=400, headers={}), body=None)
