"""
Nura - Unit tests for DrugInteractionAgent
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.healthcare.drug_interaction_agent import DrugInteractionAgent
from app.agents.base.context import AgentContext
from app.agents.healthcare.schemas import DrugInteractionAgentResponse
from app.agents.base.response import AgentResponse


@pytest.fixture
def mock_retrieval_agent():
    agent = MagicMock()
    mock_res = AgentResponse(
        success=True,
        message="Retrieval completed",
        response={
            "context": "Aspirin and Ibuprofen taken together can increase bleeding risk.",
            "retrieved_chunks": [
                {"text": "Aspirin and Ibuprofen bleeding risk details", "score": 0.95, "metadata": {"source": "drug_knowledge"}}
            ],
            "collections_used": ["drug_knowledge"]
        },
        execution_time=10.0,
        agent_name="RetrievalAgent"
    )
    agent.run = AsyncMock(return_value=mock_res)
    return agent


@pytest.fixture
def mock_patient_memory_repository():
    repo = MagicMock()
    mock_mem = MagicMock()
    mock_mem.ai_summary = "Longitudinal patient profile memory summary"
    mock_mem.chronic_conditions = ["Gastritis"]
    mock_mem.allergies = ["Penicillin"]
    mock_mem.medications = ["Lisinopril"]
    mock_mem.diagnoses = ["Gastritis"]
    repo.get_by_patient_id = AsyncMock(return_value=mock_mem)
    return repo


@pytest.fixture
def mock_ai_service():
    service = MagicMock()
    mock_res = MagicMock()
    mock_res.response = """
    {
      "interaction_found": true,
      "severity": "HIGH",
      "interaction_summary": "Taking Aspirin with Ibuprofen is associated with a high bleeding risk and worsening Gastritis.",
      "warnings": ["Increased risk of gastrointestinal bleeding"],
      "alternatives": ["Consult physician for safer pain relievers like Acetaminophen."]
    }
    """
    mock_res.prompt_tokens = 200
    mock_res.completion_tokens = 100
    mock_res.total_tokens = 300
    mock_res.estimated_cost = 0.005
    service.generate = AsyncMock(return_value=mock_res)
    return service


@pytest.mark.asyncio
async def test_drug_interaction_agent_execution(
    mock_retrieval_agent,
    mock_patient_memory_repository,
    mock_ai_service
):
    agent = DrugInteractionAgent(
        retrieval_agent=mock_retrieval_agent,
        patient_memory_repository=mock_patient_memory_repository,
        ai_service=mock_ai_service
    )
    
    ctx = AgentContext(patient_id="patient-123")
    res = await agent.run("can I take aspirin with ibuprofen?", ctx)
    
    assert res.success is True
    assert isinstance(res.response, DrugInteractionAgentResponse)
    assert res.response.interaction_found is True
    assert res.response.severity == "HIGH"
    assert "bleeding risk" in res.response.interaction_summary
    assert "gastrointestinal bleeding" in res.response.warnings[0]
    assert "Disclaimer:" in res.response.interaction_summary
    assert len(res.response.citations) == 1
    
    mock_retrieval_agent.run.assert_called_once()
    mock_patient_memory_repository.get_by_patient_id.assert_called_with("patient-123")
    mock_ai_service.generate.assert_called_once()
