"""
Nura - AI Orchestrator Unit Tests
Verifies pipeline coordination, validation, context loading, LLM calls, metrics tracking, and health aggregates.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.services.ai_orchestrator import AIOrchestrator
from app.schemas.ai import AIPlaygroundChatRequest
from app.utils.ai import orchestrator_metrics


@pytest.mark.asyncio
async def test_orchestrator_execute_chat_success():
    """Verify standard orchestrator chat run coordinates dependencies, metrics telemetry, and estimation of cost"""
    # Setup mocks
    mock_groq = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Healthy medical response."
    mock_response.choices = [mock_choice]
    mock_response.usage = MagicMock(prompt_tokens=50, completion_tokens=100, total_tokens=150)
    mock_groq.generate = AsyncMock(return_value=mock_response)
    mock_groq.settings = MagicMock()
    mock_groq.settings.GROQ_MODEL = "llama-3.3-70b-versatile"

    mock_embedding = MagicMock()
    mock_vector = MagicMock()
    
    mock_context_service = MagicMock()
    mock_context_res = MagicMock()
    mock_context_res.patient_profile = {"full_name": "John Doe"}
    mock_context_res.medical_summary = "Patient suffers from minor allergies."
    mock_context_res.current_conditions = ["Allergies"]
    mock_context_res.current_medications = ["Claritin"]
    mock_context_res.medication_allergies = []
    mock_context_res.metadata.sections_returned = ["patient_profile", "medical_summary"]
    mock_context_service.assemble_context = AsyncMock(return_value=mock_context_res)

    mock_prompt_loader = MagicMock()
    mock_prompt_loader.render = MagicMock(return_value="Rendered Prompt payload")
    mock_prompt_loader.versions = {"chat_prompt": "1.0.0"}

    # Reset metrics
    orchestrator_metrics.reset()

    orchestrator = AIOrchestrator(
        groq_service=mock_groq,
        embedding_service=mock_embedding,
        vector_service=mock_vector,
        patient_context_service=mock_context_service,
        prompt_loader=mock_prompt_loader
    )

    request = AIPlaygroundChatRequest(
        prompt="What medications can I take?",
        patient_id="patient_123",
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        max_tokens=500
    )

    res = await orchestrator.execute_chat(request, user_id="user_admin")

    assert res.response == "Healthy medical response."
    assert res.execution_session.status == "success"
    assert res.execution_session.tokens == 150
    assert res.execution_session.cost > 0.0
    assert res.prompt_template == "Rendered Prompt payload"
    assert res.patient_context_sections == ["patient_profile", "medical_summary"]

    # Verify metrics
    metrics = orchestrator_metrics.get_metrics()
    assert metrics["requests"] == 1
    assert metrics["failures"] == 0
    assert metrics["avg_tokens"] == 150
    assert metrics["total_cost"] > 0.0
    assert metrics["model_usage"]["llama-3.3-70b-versatile"] == 1


@pytest.mark.asyncio
async def test_orchestrator_execute_chat_empty_prompt():
    """Verify validation aborts execution session immediately if user prompt is empty"""
    mock_groq = MagicMock()
    mock_groq.settings = MagicMock()
    mock_groq.settings.GROQ_MODEL = "llama-3.3-70b-versatile"
    mock_embedding = MagicMock()
    mock_vector = MagicMock()
    mock_context_service = MagicMock()
    mock_prompt_loader = MagicMock()

    orchestrator = AIOrchestrator(
        groq_service=mock_groq,
        embedding_service=mock_embedding,
        vector_service=mock_vector,
        patient_context_service=mock_context_service,
        prompt_loader=mock_prompt_loader
    )

    request = AIPlaygroundChatRequest(prompt="   ", patient_id=None)
    res = await orchestrator.execute_chat(request)

    assert res.response == ""
    assert res.execution_session.status == "failed"
    assert res.execution_session.errors == "User prompt cannot be empty"
    
    mock_groq.generate.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_execute_chat_context_builder_error():
    """Verify context compilation error does not crash lifecycle and continues with fallback string"""
    mock_groq = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Fallback Response"
    mock_response.choices = [mock_choice]
    mock_response.usage = None
    mock_groq.generate = AsyncMock(return_value=mock_response)
    mock_groq.settings = MagicMock()
    mock_groq.settings.GROQ_MODEL = "llama-3.3-70b-versatile"

    mock_embedding = MagicMock()
    mock_vector = MagicMock()
    
    mock_context_service = MagicMock()
    mock_context_service.assemble_context = AsyncMock(side_effect=Exception("Database Timeout"))

    mock_prompt_loader = MagicMock()
    mock_prompt_loader.render = MagicMock(return_value="Rendered Prompt payload")

    orchestrator = AIOrchestrator(
        groq_service=mock_groq,
        embedding_service=mock_embedding,
        vector_service=mock_vector,
        patient_context_service=mock_context_service,
        prompt_loader=mock_prompt_loader
    )

    request = AIPlaygroundChatRequest(prompt="Test fallback", patient_id="patient_fail")
    res = await orchestrator.execute_chat(request)

    assert res.response == "Fallback Response"
    assert res.execution_session.status == "success"
    
    # Assert prompt loader was rendered with error context
    mock_prompt_loader.render.assert_any_call(
        name="medical_assistant",
        variables={"patient_context": "Error compiling patient context."},
        is_system=True
    )


@pytest.mark.asyncio
async def test_orchestrator_execute_chat_prompt_loader_error():
    """Verify prompt rendering errors are handled gracefully returning failed execution session"""
    mock_groq = MagicMock()
    mock_groq.settings = MagicMock()
    mock_groq.settings.GROQ_MODEL = "llama-3.3-70b-versatile"
    mock_embedding = MagicMock()
    mock_vector = MagicMock()
    mock_context_service = MagicMock()
    
    mock_prompt_loader = MagicMock()
    mock_prompt_loader.render = MagicMock(side_effect=ValueError("Missing placeholders: ['user_query']"))

    orchestrator = AIOrchestrator(
        groq_service=mock_groq,
        embedding_service=mock_embedding,
        vector_service=mock_vector,
        patient_context_service=mock_context_service,
        prompt_loader=mock_prompt_loader
    )

    request = AIPlaygroundChatRequest(prompt="Fail rendering", patient_id=None)
    res = await orchestrator.execute_chat(request)

    assert res.response == ""
    assert res.execution_session.status == "failed"
    assert "Prompt template rendering failed" in res.execution_session.errors
    
    mock_groq.generate.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_execute_chat_groq_error():
    """Verify LLM failure catches exceptions and sets failed execution session details"""
    mock_groq = MagicMock()
    mock_groq.generate = AsyncMock(side_effect=Exception("API limit reached"))
    mock_groq.settings = MagicMock()
    mock_groq.settings.GROQ_MODEL = "llama-3.3-70b-versatile"

    mock_embedding = MagicMock()
    mock_vector = MagicMock()
    mock_context_service = MagicMock()
    mock_prompt_loader = MagicMock()
    mock_prompt_loader.render = MagicMock(return_value="Payload")

    orchestrator = AIOrchestrator(
        groq_service=mock_groq,
        embedding_service=mock_embedding,
        vector_service=mock_vector,
        patient_context_service=mock_context_service,
        prompt_loader=mock_prompt_loader
    )

    request = AIPlaygroundChatRequest(prompt="Fail LLM", patient_id=None)
    res = await orchestrator.execute_chat(request)

    assert res.response == ""
    assert res.execution_session.status == "failed"
    assert "LLM generation failed: API limit reached" in res.execution_session.errors


@pytest.mark.asyncio
async def test_orchestrator_health_check():
    """Verify consolidated health auditing returns correct nested connectivity check structure"""
    mock_groq = MagicMock()
    mock_groq.health_check = AsyncMock(return_value={"reachable": True, "model": "llama3", "latency_ms": 50})
    
    mock_embedding = MagicMock()
    mock_embedding.health_check = AsyncMock(return_value={"status": "healthy", "provider": "local"})

    mock_vector = MagicMock()
    mock_vector.health = AsyncMock(return_value={"connected": True, "status": "healthy", "collections": []})

    mock_context_service = MagicMock()
    mock_context_service.user_repository = MagicMock()
    mock_context_service.user_repository.exists = AsyncMock(return_value=True)

    mock_prompt_loader = MagicMock()
    mock_prompt_loader.get_template = MagicMock(return_value="Content")
    mock_prompt_loader.versions = {"chat_prompt": "1.0.0"}

    orchestrator = AIOrchestrator(
        groq_service=mock_groq,
        embedding_service=mock_embedding,
        vector_service=mock_vector,
        patient_context_service=mock_context_service,
        prompt_loader=mock_prompt_loader
    )

    health = await orchestrator.health_check()

    assert health["groq"]["reachable"] is True
    assert health["embedding"]["status"] == "healthy"
    assert health["vector"]["connected"] is True
    assert health["prompt_registry"]["status"] == "healthy"
    assert health["prompt_registry"]["templates_count"] == 1
    assert health["context_builder"]["status"] == "healthy"
