"""
Nura - Unit tests for SymptomAgent
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from app.agents.core.symptom_agent import SymptomAgent
from app.agents.base.context import AgentContext
from app.agents.core.schemas import SymptomAgentResponse
from app.agents.base.response import AgentResponse


@pytest.fixture
def mock_retrieval_agent():
    agent = MagicMock()
    mock_res = AgentResponse(
        success=True,
        message="Retrieval completed",
        response={
            "context": "Chest pain indicators and cardiovascular conditions guidelines.",
            "retrieved_chunks": [
                {"text": "Sharp chest pain radiates to arm", "score": 0.90, "metadata": {"source": "symptoms_guide"}}
            ],
            "collections_used": ["medical_knowledge"]
        },
        execution_time=10.0,
        agent_name="RetrievalAgent"
    )
    agent.run = AsyncMock(return_value=mock_res)
    return agent


@pytest.fixture
def mock_patient_context_service():
    service = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.patient_profile = {"full_name": "Jane Doe"}
    mock_ctx.medical_summary = "History of hypercholesterolemia."
    mock_ctx.current_conditions = []
    mock_ctx.current_medications = []
    mock_ctx.medication_allergies = []
    service.assemble_context = AsyncMock(return_value=mock_ctx)
    return service


@pytest.fixture
def mock_ai_service():
    service = MagicMock()
    mock_res = MagicMock()
    mock_res.response = json.dumps({
        "summary": "Mild symptom guidance notes.",
        "possible_causes": ["Heartburn", "Angina"],
        "red_flags": ["Chest discomfort radiating to left shoulder"],
        "recommended_action": "Seek professional doctor checkup.",
        "emergency": True
    })
    mock_res.prompt_tokens = 200
    mock_res.completion_tokens = 80
    mock_res.total_tokens = 280
    mock_res.estimated_cost = 0.004
    service.generate = AsyncMock(return_value=mock_res)
    return service


@pytest.mark.asyncio
async def test_symptom_agent_execution(
    mock_retrieval_agent,
    mock_patient_context_service,
    mock_ai_service
):
    agent = SymptomAgent(
        retrieval_agent=mock_retrieval_agent,
        patient_context_service=mock_patient_context_service,
        ai_service=mock_ai_service
    )
    
    ctx = AgentContext(patient_id="patient-456")
    res = await agent.run("sharp pain in left chest", ctx)
    
    assert res.success is True
    assert isinstance(res.response, SymptomAgentResponse)
    assert res.response.emergency is True
    assert "disclaimer" in res.response.summary.lower() or "informational purposes only" in res.response.summary.lower()
    assert "critical warning" in res.response.recommended_action.lower()
    assert "Angina" in res.response.possible_causes
    assert len(res.response.red_flags) == 1
    assert res.response.usage["total_tokens"] == 280
    
    mock_retrieval_agent.run.assert_called_once()
    mock_patient_context_service.assemble_context.assert_called_with("patient-456")
    mock_ai_service.generate.assert_called_once()
