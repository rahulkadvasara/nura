"""
Nura - Unit tests for Production MemoryAgent
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.core.memory_agent import MemoryAgent
from app.agents.base.context import AgentContext
from app.agents.core.schemas import MemoryAgentResponse


@pytest.fixture
def mock_patient_memory_repo():
    repo = MagicMock()
    mock_memory = MagicMock()
    mock_memory.ai_summary = "Longitudinal medical history summary"
    mock_memory.chronic_conditions = ["Diabetes"]
    mock_memory.allergies = ["Penicillin"]
    mock_memory.medications = ["Metformin"]
    mock_memory.surgeries = []
    mock_memory.diagnoses = []
    mock_memory.summary_version = 2
    repo.get_by_patient_id = AsyncMock(return_value=mock_memory)
    return repo


@pytest.fixture
def mock_chat_msg_repo():
    repo = MagicMock()
    mock_msg = MagicMock()
    mock_msg.model_dump.return_value = {"role": "user", "content": "Query"}
    repo.get_latest_messages = AsyncMock(return_value=[mock_msg])
    return repo


@pytest.fixture
def mock_retrieval_service():
    service = MagicMock()
    service.retrieve_multiple = AsyncMock(return_value={
        "results": [{"content": "Matched vector text", "score": 0.85}]
    })
    return service


@pytest.fixture
def mock_memory_sync_service():
    service = MagicMock()
    service.sync_patient = AsyncMock(return_value={"success": True, "rebuilt": True})
    return service


@pytest.mark.asyncio
async def test_memory_agent_execution(
    mock_patient_memory_repo,
    mock_chat_msg_repo,
    mock_retrieval_service,
    mock_memory_sync_service
):
    agent = MemoryAgent(
        patient_memory_repository=mock_patient_memory_repo,
        chat_message_repository=mock_chat_msg_repo,
        retrieval_service=mock_retrieval_service,
        memory_sync_service=mock_memory_sync_service
    )
    
    ctx = AgentContext(
        patient_id="patient-123",
        session_id="session-456"
    )
    
    res = await agent.run("recall allergies", ctx)
    
    assert res.success is True
    assert isinstance(res.response, MemoryAgentResponse)
    assert res.response.memory_summary == "Longitudinal medical history summary"
    assert len(res.response.conversation_history) == 1
    assert "Diabetes" in res.response.patient_summary
    assert len(res.response.relevant_context) == 1
    assert res.response.relevant_context[0]["content"] == "Matched vector text"
    
    # Assert mocks were called
    mock_patient_memory_repo.get_by_patient_id.assert_called_with("patient-123")
    mock_memory_sync_service.sync_patient.assert_called_with("patient-123")
