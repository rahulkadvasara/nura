"""
Nura - Unit tests for MemoryAgent
"""

import pytest
from typing import List, Dict, Any, Optional

from app.core.ai_config import AISettings
from app.agents import MemoryAgent, AgentContext, AgentResponse


@pytest.fixture
def mock_settings():
    return AISettings(
        GROQ_API_KEY="test_key",
        GROQ_MODEL="llama-3.3-70b-versatile",
        TIMEOUT_SECONDS=0.1,
        MAX_RETRIES=0,
        RETRY_MIN_DELAY=0.01,
        RETRY_MAX_DELAY=0.02
    )


class CustomMemoryAgent(MemoryAgent):
    """Concrete subclass of MemoryAgent overriding get/update memory hooks"""

    async def get_patient_memory(self, patient_id: str) -> Optional[Dict[str, Any]]:
        if patient_id == "pt-exists":
            return {
                "patient_id": patient_id,
                "ai_summary": "Known patient summary",
                "allergies": ["Peanuts"]
            }
        return None

    async def update_patient_memory(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        return patient_id == "pt-exists"

    async def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return [{"role": "user", "content": "hello msg"}]


@pytest.mark.asyncio
async def test_memory_agent_default_implementation_empty_context(mock_settings):
    """Verify default MemoryAgent execute with empty context returns None and empty citations"""
    agent = MemoryAgent(settings=mock_settings)
    ctx = AgentContext()
    
    response = await agent.run("some query", ctx)
    
    assert response.success is True
    assert response.response is None
    assert response.citations == []
    assert response.metadata["has_memory"] is False


@pytest.mark.asyncio
async def test_memory_agent_default_implementation_with_patient(mock_settings):
    """Verify default MemoryAgent execute with patient ID returns None but includes memory citations"""
    agent = MemoryAgent(settings=mock_settings)
    ctx = AgentContext(patient_id="pt-123")
    
    response = await agent.run("some query", ctx)
    
    assert response.success is True
    assert response.response is None
    assert response.citations == ["memory://patient/pt-123"]
    assert response.metadata["has_memory"] is False


@pytest.mark.asyncio
async def test_memory_agent_custom_subclass(mock_settings):
    """Verify custom MemoryAgent subclass overrides memory methods successfully"""
    agent = CustomMemoryAgent(name="Clinical Memory Keeper", settings=mock_settings)
    
    # 1. Test get memory for existing patient
    ctx1 = AgentContext(patient_id="pt-exists")
    response1 = await agent.run("get profile", ctx1)
    
    assert response1.success is True
    assert response1.agent_name == "Clinical Memory Keeper"
    assert response1.response["patient_id"] == "pt-exists"
    assert response1.response["allergies"] == ["Peanuts"]
    assert response1.citations == ["memory://patient/pt-exists"]
    assert response1.metadata["has_memory"] is True
    
    # 2. Test hooks directly
    update_ok = await agent.update_patient_memory("pt-exists", {"allergies": []})
    assert update_ok is True
    
    history = await agent.get_conversation_history("session-123")
    assert len(history) == 1
    assert history[0]["content"] == "hello msg"
