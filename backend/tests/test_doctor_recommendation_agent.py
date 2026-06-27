"""
Nura - Unit tests for DoctorRecommendationAgent
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.healthcare.doctor_recommendation_agent import DoctorRecommendationAgent
from app.agents.base.context import AgentContext
from app.agents.healthcare.schemas import DoctorRecommendationAgentResponse
from app.agents.base.response import AgentResponse


@pytest.fixture
def mock_retrieval_agent():
    agent = MagicMock()
    mock_res = AgentResponse(
        success=True,
        message="Retrieval completed",
        response={
            "context": "Dr. Sarah Smith is a highly experienced Cardiologist.",
            "retrieved_chunks": [
                {
                    "text": "Dr. Sarah Smith Cardiologist profile",
                    "score": 0.98,
                    "payload": {
                        "doctor_id": "doc-555",
                        "full_name": "Dr. Sarah Smith",
                        "specialization": "Cardiology",
                        "experience_years": 15,
                        "languages": ["English"],
                        "hospital": "Nura General Hospital"
                    }
                }
            ],
            "collections_used": ["doctor_knowledge"]
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
    mock_ctx.patient_profile = {"full_name": "John Doe", "location": "New York"}
    mock_ctx.medical_summary = "Pre-diabetic history."
    mock_ctx.current_conditions = []
    service.assemble_context = AsyncMock(return_value=mock_ctx)
    return service


@pytest.fixture
def mock_doctor_availability_repository():
    repo = MagicMock()
    mock_slot = MagicMock()
    mock_slot.day_of_week = "Monday"
    mock_slot.start_time = "09:00"
    mock_slot.end_time = "12:00"
    repo.get_active_by_doctor_id = AsyncMock(return_value=[mock_slot])
    return repo


@pytest.fixture
def mock_ai_service():
    service = MagicMock()
    mock_res = MagicMock()
    mock_res.response = """
    {
      "recommended_doctors": [
        {
          "doctor_id": "doc-555",
          "full_name": "Dr. Sarah Smith",
          "specialization": "Cardiology",
          "hospital": "Nura General Hospital",
          "experience_years": 15,
          "languages": ["English"],
          "availability": "Monday: 09:00-12:00",
          "match_reason": "Top rated cardiologist near your location with Monday slots available."
        }
      ],
      "reasoning": "Sarah Smith matched Cardiology criteria perfectly.",
      "matching_specialization": "Cardiology",
      "confidence": 0.98
    }
    """
    mock_res.prompt_tokens = 200
    mock_res.completion_tokens = 100
    mock_res.total_tokens = 300
    mock_res.estimated_cost = 0.005
    service.generate = AsyncMock(return_value=mock_res)
    return service


@pytest.mark.asyncio
async def test_doctor_recommendation_agent_execution(
    mock_retrieval_agent,
    mock_patient_context_service,
    mock_doctor_availability_repository,
    mock_ai_service
):
    agent = DoctorRecommendationAgent(
        retrieval_agent=mock_retrieval_agent,
        patient_context_service=mock_patient_context_service,
        doctor_availability_repository=mock_doctor_availability_repository,
        ai_service=mock_ai_service
    )
    
    ctx = AgentContext(patient_id="patient-123")
    res = await agent.run("I need a cardiologist for chest tightness.", ctx)
    
    assert res.success is True
    assert isinstance(res.response, DoctorRecommendationAgentResponse)
    assert len(res.response.recommended_doctors) == 1
    assert res.response.recommended_doctors[0]["full_name"] == "Dr. Sarah Smith"
    assert res.response.recommended_doctors[0]["availability"] == "Monday: 09:00-12:00"
    assert res.response.matching_specialization == "Cardiology"
    assert res.response.confidence == 0.98
    
    mock_retrieval_agent.run.assert_called_once()
    mock_patient_context_service.assemble_context.assert_called_with("patient-123")
    mock_doctor_availability_repository.get_active_by_doctor_id.assert_called_with("doc-555")
    mock_ai_service.generate.assert_called_once()
