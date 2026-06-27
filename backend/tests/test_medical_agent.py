"""
Nura - Unit tests for MedicalKnowledgeAgent
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.core.medical_knowledge_agent import MedicalKnowledgeAgent
from app.agents.base.context import AgentContext
from app.agents.core.schemas import MedicalKnowledgeAgentResponse
from app.agents.base.response import AgentResponse


@pytest.fixture
def mock_retrieval_agent():
    agent = MagicMock()
    mock_res = AgentResponse(
        success=True,
        message="Retrieval completed",
        response={
            "context": "Diabetes mellitus management clinical guidelines.",
            "retrieved_chunks": [
                {"text": "Diabetes mellitus management", "score": 0.95, "metadata": {"source": "guidelines"}}
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
    mock_ctx.patient_profile = {"full_name": "John Doe"}
    mock_ctx.medical_summary = "Pre-diabetic condition history."
    mock_ctx.current_conditions = ["Hypertension"]
    mock_ctx.current_medications = []
    mock_ctx.medication_allergies = []
    mock_ctx.past_medical_history = []
    service.assemble_context = AsyncMock(return_value=mock_ctx)
    return service


@pytest.fixture
def mock_ai_service():
    service = MagicMock()
    mock_res = MagicMock()
    mock_res.response = "Under guidelines, diabetes mellitus is managed via insulin and lifestyle changes."
    mock_res.prompt_tokens = 150
    mock_res.completion_tokens = 50
    mock_res.total_tokens = 200
    mock_res.estimated_cost = 0.003
    service.generate = AsyncMock(return_value=mock_res)
    return service


@pytest.mark.asyncio
async def test_medical_knowledge_agent_execution(
    mock_retrieval_agent,
    mock_patient_context_service,
    mock_ai_service
):
    agent = MedicalKnowledgeAgent(
        retrieval_agent=mock_retrieval_agent,
        patient_context_service=mock_patient_context_service,
        ai_service=mock_ai_service
    )
    
    ctx = AgentContext(patient_id="patient-123")
    res = await agent.run("how to manage diabetes?", ctx)
    
    assert res.success is True
    assert isinstance(res.response, MedicalKnowledgeAgentResponse)
    assert "insulin" in res.response.answer
    assert len(res.response.citations) == 1
    assert res.response.citations[0]["source"] == "guidelines"
    assert res.response.sources == ["medical_knowledge"]
    assert res.response.usage["total_tokens"] == 200
    
    mock_retrieval_agent.run.assert_called_once()
    mock_patient_context_service.assemble_context.assert_called_with("patient-123")
    mock_ai_service.generate.assert_called_once()
