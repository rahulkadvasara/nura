"""
Nura - Conversation Intelligence Tests
Verifies suggested followups generation and auto-naming routines
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.models.chat import (
    ChatSessionInDB,
    SessionStatus,
)
from app.services.chat.conversation_intelligence import ConversationIntelligenceService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_generate_intelligence_success():
    groq_service = AsyncMock()
    
    # Mock LLM choices payload containing json string
    class MockChoice:
        message = MagicMock(content='{"suggested_questions":["What is flu?","Do I have fever?"],"title":"Flu Checkup","tags":["Flu"],"quality_score":0.95}')
    class MockResponse:
        choices = [MockChoice()]
        
    groq_service.generate_json = AsyncMock(return_value=MockResponse())

    service = ConversationIntelligenceService(
        groq_service=groq_service,
        chat_session_repository=AsyncMock()
    )

    intel = await service.generate_intelligence("Check symptoms", "You have flu.")

    assert len(intel["suggested_questions"]) == 2
    assert intel["suggested_questions"][0] == "What is flu?"
    assert intel["title"] == "Flu Checkup"
    assert intel["quality_score"] == 0.95


@pytest.mark.asyncio
async def test_update_session_title_if_untitled():
    session_repo = AsyncMock()
    session = ChatSessionInDB(
        id="sess123",
        patient_id="pat123",
        title="New Chat",  # Generic placeholder
        status=SessionStatus.ACTIVE,
        session_type="ai_chat",
        active=True,
        last_message_at=utc_now(),
        message_count=2,
        total_tokens=0,
        total_cost=0.0,
        pinned=False,
        archived=False,
        metadata={},
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    session_repo.get = AsyncMock(return_value=session)
    session_repo.update = AsyncMock()

    service = ConversationIntelligenceService(
        groq_service=AsyncMock(),
        chat_session_repository=session_repo
    )

    await service.update_session_title_if_untitled("sess123", "Heart Consultation")

    # Verifies session title gets renamed
    session_repo.update.assert_called_once()
    args, kwargs = session_repo.update.call_args
    update_arg = args[1]
    assert update_arg.title == "Heart Consultation"
