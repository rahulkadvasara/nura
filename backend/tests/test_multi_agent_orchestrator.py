"""
Nura - Unit tests for MultiAgentOrchestrator
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator, get_multi_agent_telemetry
from app.schemas.orchestrator import AIExecuteRequest, StandardResponseContract
from app.graph.state import GraphState


@pytest.fixture
def mock_graph_engine():
    engine = MagicMock()
    mock_state_dict = {
        "request_id": "test-req-123",
        "session_id": "session-123",
        "conversation_id": "conv-123",
        "patient_id": "patient-123",
        "query": "Hello",
        "detected_intent": "MEDICAL_KNOWLEDGE",
        "selected_agent": "MedicalKnowledgeAgent",
        "response": "Hello, I am your medical knowledge agent.",
        "citations": [{"source": "medical_doc_1", "text": "reference text", "score": 0.95}],
        "execution_trace": ["__start__", "initialize_state", "router_agent", "intent_detection", "MedicalKnowledgeAgent", "__finish__"],
        "token_usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        "execution_time": 120.5,
        "metadata": {
            "model": "llama-3-groq-70b-tool-use-preview",
            "estimated_cost": 0.0004
        }
    }
    engine.execute_async = AsyncMock(return_value=mock_state_dict)
    return engine


@pytest.mark.asyncio
async def test_multi_agent_orchestrator_execute_success(mock_graph_engine):
    orchestrator = MultiAgentOrchestrator(engine=mock_graph_engine)
    
    # Initialize telemetry
    telemetry = get_multi_agent_telemetry()
    telemetry.reset()

    request = AIExecuteRequest(
        query="Hello",
        patient_id="patient-123",
        session_id="session-123",
        conversation_id="conv-123"
    )

    response = await orchestrator.execute(request, user_id="user-123", role="patient")

    assert isinstance(response, StandardResponseContract)
    assert response.success is True
    assert response.agent == "MedicalKnowledgeAgent"
    assert response.intent == "MEDICAL_KNOWLEDGE"
    assert "medical knowledge agent" in response.response
    assert len(response.citations) == 1
    assert response.cost == 0.0004
    assert response.usage["total_tokens"] == 150
    assert response.execution_time >= 0.0
    
    # Verify telemetry aggregation
    stats = telemetry.get_stats()
    assert stats["total_executions"] == 1
    assert stats["intent_distribution"]["MEDICAL_KNOWLEDGE"] == 1
    assert stats["agent_usage"]["MedicalKnowledgeAgent"] == 1
    assert stats["failures"] == 0


@pytest.mark.asyncio
async def test_multi_agent_orchestrator_crashed_fallback(mock_graph_engine):
    mock_graph_engine.execute_async = AsyncMock(side_effect=ValueError("Graph timeout error!"))
    orchestrator = MultiAgentOrchestrator(engine=mock_graph_engine)
    
    request = AIExecuteRequest(
        query="Hello",
        patient_id="patient-123"
    )

    response = await orchestrator.execute(request, user_id="user-123", role="patient")

    assert response.success is False
    assert "Graph timeout error!" in response.response
    assert response.intent == "ERROR"
    assert response.agent is None
    assert len(response.warnings) == 1
