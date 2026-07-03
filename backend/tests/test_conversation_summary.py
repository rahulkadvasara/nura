"""
Nura - Conversation Summary Service Tests
Verifies clinical summary creation and medical concept extraction pipelines
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.chat_memory.conversation_summary_service import ConversationSummaryService


@pytest.mark.asyncio
async def test_generate_summary_success():
    groq_service = AsyncMock()
    
    # Mock LLM choices payload containing json string
    class MockChoice:
        message = MagicMock(content='{"summary":"Patient has headache.","keywords":["headache"],"entities":["headache"],"medications":[],"symptoms":["headache"],"diagnoses":[],"recommendations":[],"followups":[]}')
    class MockResponse:
        choices = [MockChoice()]
        
    groq_service.generate_json = AsyncMock(return_value=MockResponse())

    service = ConversationSummaryService(groq_service=groq_service)

    messages = [
        {"role": "user", "content": "I have headache."}
    ]

    res = await service.generate_summary(messages)

    assert res["summary"] == "Patient has headache."
    assert "headache" in res["keywords"]
    assert "headache" in res["symptoms"]
