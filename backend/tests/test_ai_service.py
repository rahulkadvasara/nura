"""
Nura - AI Service Unit Tests
Verifies orchestration layer response mapping, latency accounting, estimated cost calculation, and in-memory metrics.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.ai_service import AIService
from app.utils.ai import ai_metrics


@pytest.mark.asyncio
async def test_ai_service_generate_success():
    """Verify AIService normalizes LLM outputs and records telemetry metrics correctly upon success"""
    # Setup mock GroqService dependencies
    mock_groq = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Sample generated response text."
    mock_choice.finish_reason = "stop"
    mock_response.choices = [mock_choice]
    mock_response.usage = MagicMock(prompt_tokens=100, completion_tokens=200, total_tokens=300)
    
    mock_groq.generate = AsyncMock(return_value=mock_response)
    mock_groq.settings = MagicMock()
    mock_groq.settings.GROQ_MODEL = "llama-3.3-70b-versatile"
    
    # Reset in-memory trackers
    ai_metrics.reset()
    
    service = AIService(groq_service=mock_groq)
    response = await service.generate(prompt="Explain healthcare AI infrastructure.")
    
    assert response.response == "Sample generated response text."
    assert response.model == "llama-3.3-70b-versatile"
    assert response.prompt_tokens == 100
    assert response.completion_tokens == 200
    assert response.total_tokens == 300
    assert response.finish_reason == "stop"
    assert response.latency_ms >= 0
    assert response.estimated_cost > 0
    
    # Verify in-memory performance statistics were updated
    metrics = ai_metrics.get_metrics()
    assert metrics["requests"] == 1
    assert metrics["failures"] == 0
    assert metrics["avg_tokens"] == 300


@pytest.mark.asyncio
async def test_ai_service_generate_failure():
    """Verify AIService logs failure events and triggers metric indicators when errors occur"""
    mock_groq = MagicMock()
    mock_groq.generate = AsyncMock(side_effect=ValueError("Test Failure Exception"))
    mock_groq.settings = MagicMock()
    mock_groq.settings.GROQ_MODEL = "llama-3.3-70b-versatile"
    
    # Reset in-memory trackers
    ai_metrics.reset()
    
    service = AIService(groq_service=mock_groq)
    with pytest.raises(ValueError):
        await service.generate(prompt="Fail this request.")
        
    # Verify failure rate stats are captured
    metrics = ai_metrics.get_metrics()
    assert metrics["requests"] == 1
    assert metrics["failures"] == 1
