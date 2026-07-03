import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.services.chat.conversation_intelligence import ConversationIntelligenceService
from app.models.chat import ChatSessionInDB, ChatMessageInDB, MessageRole, SessionStatus

@pytest.mark.asyncio
async def test_auto_update_session_metadata():
    groq_service = AsyncMock()
    session_repo = AsyncMock()
    message_repo = MagicMock()
    
    # Mock groq response structure
    mock_choice = MagicMock()
    mock_choice.message.content = '{"title": "Flu Diagnostic Check", "summary": "Patient reports influenza symptoms.", "tags": ["Flu", "Symptoms"], "last_topic": "Flu checks", "category": "Symptoms", "suggested_questions": ["What med is safe?", "When to see doctor?"], "quality_score": 0.98}'
    
    groq_result = MagicMock()
    groq_result.choices = [mock_choice]
    groq_service.generate_json.return_value = groq_result
    
    # Real session
    session = ChatSessionInDB(
        id="sess1",
        patient_id="pat1",
        title="New Chat",
        description="",
        status=SessionStatus.ACTIVE,
        session_type="ai_chat",
        active=True,
        last_message_at=datetime.now(timezone.utc),
        message_count=0,
        total_tokens=0,
        total_cost=0.0,
        last_agent_used=None,
        pinned=False,
        archived=False,
        metadata={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    session_repo.get.return_value = session
    
    # Real messages
    msg1 = ChatMessageInDB(
        id="msg1",
        session_id="sess1",
        patient_id="pat1",
        role=MessageRole.USER,
        content="I feel like I have the flu.",
        citations=[],
        attachments=[],
        token_usage={},
        metadata={},
        deleted=False,
        created_at=datetime.now(timezone.utc)
    )
    
    msg2 = ChatMessageInDB(
        id="msg2",
        session_id="sess1",
        patient_id="pat1",
        role=MessageRole.ASSISTANT,
        content="Make sure to monitor your temperature.",
        citations=[],
        attachments=[],
        token_usage={},
        metadata={},
        deleted=False,
        created_at=datetime.now(timezone.utc)
    )
    
    message_repo.get_by_session_id = AsyncMock(return_value=[msg1, msg2])
    
    service = ConversationIntelligenceService(groq_service, session_repo, message_repo)
    res = await service.auto_update_session_metadata("sess1")
    
    assert res["title"] == "Flu Diagnostic Check"
    assert res["category"] == "Symptoms"
    session_repo.update.assert_called_once()
    
    # Check that update payload had the metadata fields
    args, _ = session_repo.update.call_args
    update_payload = args[1]
    assert update_payload.title == "Flu Diagnostic Check"
    assert update_payload.metadata["summary"] == "Patient reports influenza symptoms."
    assert update_payload.metadata["category"] == "Symptoms"
