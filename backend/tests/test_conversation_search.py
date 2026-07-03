import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.services.chat.conversation_search_service import ConversationSearchService, highlight_text
from app.models.chat import ChatSessionInDB, ChatMessageInDB, MessageRole

def test_highlight_text():
    text = "The patient shows flu symptoms and needs rest."
    res = highlight_text(text, "flu")
    assert "<mark>flu</mark>" in res.lower()
    
    # Check bounds context window
    res_context = highlight_text("A very long prefix text context to shift the window. The patient has flu symptoms here.", "flu")
    assert "..." in res_context

@pytest.mark.asyncio
async def test_search_conversations_hits_messages_and_sessions():
    session_repo = MagicMock()
    message_repo = MagicMock()
    
    # Mock database session document query cursor
    session_doc = {
        "_id": "sess1",
        "patient_id": "pat1",
        "title": "Heart Diagnosis Consultation",
        "description": "Cardiology diagnostic review",
        "status": "ACTIVE",
        "session_type": "ai_chat",
        "active": True,
        "last_message_at": datetime.now(timezone.utc),
        "message_count": 2,
        "total_tokens": 100,
        "total_cost": 0.05,
        "last_agent_used": "CardiologyAgent",
        "pinned": True,
        "archived": False,
        "metadata": {"summary": "Discussed chest pain."},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    class MockCursor:
        def __init__(self, docs):
            self.docs = docs
        async def to_list(self, length=1000):
            return self.docs
            
    session_repo.collection = MagicMock()
    session_repo.collection.find.return_value = MockCursor([session_doc])
    session_repo.model_class = ChatSessionInDB
    
    # Mock message hits
    message_doc = {
        "_id": "msg1",
        "session_id": "sess1",
        "patient_id": "pat1",
        "role": "ASSISTANT",
        "content": "Check your chest pain indicators.",
        "citations": [],
        "attachments": [],
        "token_usage": {},
        "metadata": {},
        "deleted": False,
        "created_at": datetime.now(timezone.utc)
    }
    message_repo.collection = MagicMock()
    message_repo.collection.find.return_value = MockCursor([message_doc])
    message_repo.model_class = ChatMessageInDB
    
    service = ConversationSearchService(session_repo, message_repo)
    res = await service.search_conversations(patient_id="pat1", query="pain")
    
    # We should have hits
    assert len(res.results) >= 2
    assert any("<mark>pain</mark>" in r.highlighted_snippet.lower() for r in res.results)
