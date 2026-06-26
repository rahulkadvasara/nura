"""
Nura - Unit tests for RetrievalAgent
"""

import pytest
from typing import List, Dict, Any, Optional

from app.core.ai_config import AISettings
from app.agents import RetrievalAgent, AgentContext, AgentResponse


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


class CustomKnowledgeRetrievalAgent(RetrievalAgent):
    """Concrete subclass of RetrievalAgent overriding retrieve hook"""
    
    async def retrieve(
        self,
        query: str,
        collection: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        return [
            {"id": "doc-1", "content": f"Found medical data for query '{query}' in '{collection}'"},
            {"id": "doc-2", "content": "Sample dosage details"}
        ]


@pytest.mark.asyncio
async def test_retrieval_agent_default_implementation(mock_settings):
    """Verify default RetrievalAgent execution behavior returns empty lists and citations"""
    agent = RetrievalAgent(settings=mock_settings)
    ctx = AgentContext(metadata={"collection": "reports"})
    
    response = await agent.run("systolic pressure logs", ctx)
    
    assert response.success is True
    assert response.agent_name == "Retrieval Agent"
    assert response.response == []
    assert response.citations == ["retrieval://reports?q=systolic pressure logs"]
    assert response.metadata["results_count"] == 0


@pytest.mark.asyncio
async def test_retrieval_agent_custom_subclass(mock_settings):
    """Verify that concrete RetrievalAgent subclasses can override retrieve behavior successfully"""
    agent = CustomKnowledgeRetrievalAgent(name="Knowledge Finder", settings=mock_settings)
    ctx = AgentContext(metadata={"collection": "medical_knowledge"})
    
    response = await agent.run("hypertension guidelines", ctx)
    
    assert response.success is True
    assert response.agent_name == "Knowledge Finder"
    assert len(response.response) == 2
    assert response.response[0]["id"] == "doc-1"
    assert "Found medical data for query 'hypertension guidelines'" in response.response[0]["content"]
    assert response.citations == ["retrieval://medical_knowledge?q=hypertension guidelines"]
    assert response.metadata["results_count"] == 2
