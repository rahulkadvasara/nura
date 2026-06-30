"""
Nura - Chat Context Builder Tests
Unit tests for build_conversation_context utility
"""

import pytest
from unittest.mock import AsyncMock
from app.models.chat import ChatMessageInDB, MessageRole
from app.services.chat.context_builder import build_conversation_context
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_build_conversation_context_formatting():
    # Mock ChatMessageRepository
    repo = AsyncMock()
    
    mock_messages = [
        ChatMessageInDB(
            id="msg1",
            session_id="sess1",
            patient_id="pat1",
            role=MessageRole.USER,
            content="Hello",
            citations=[],
            attachments=[],
            token_usage={},
            deleted=False,
            created_at=utc_now()
        ),
        ChatMessageInDB(
            id="msg2",
            session_id="sess1",
            patient_id="pat1",
            role=MessageRole.ASSISTANT,
            content="Hi patient!",
            citations=[],
            attachments=[],
            token_usage={},
            deleted=False,
            created_at=utc_now()
        )
    ]
    repo.get_by_session_id = AsyncMock(return_value=mock_messages)
    
    context = await build_conversation_context(
        chat_message_repository=repo,
        session_id="sess1",
        current_message="Is it cold?",
        session_metadata={"description": "Cold & flu query"},
        limit=20
    )
    
    # 2 messages + 1 system context instruction at index 0 = 3 items
    assert len(context) == 3
    assert context[0]["role"] == "system"
    assert "Cold & flu query" in context[0]["content"]
    assert context[1]["role"] == "user"
    assert context[1]["content"] == "Hello"
    assert context[2]["role"] == "assistant"
    assert context[2]["content"] == "Hi patient!"
    
    repo.get_by_session_id.assert_called_once_with(
        session_id="sess1",
        limit=20,
        skip=0,
        include_deleted=False
    )


@pytest.mark.asyncio
async def test_build_conversation_context_no_metadata():
    repo = AsyncMock()
    mock_messages = [
        ChatMessageInDB(
            id="msg1",
            session_id="sess1",
            patient_id="pat1",
            role=MessageRole.USER,
            content="Hello",
            citations=[],
            attachments=[],
            token_usage={},
            deleted=False,
            created_at=utc_now()
        )
    ]
    repo.get_by_session_id = AsyncMock(return_value=mock_messages)

    context = await build_conversation_context(
        chat_message_repository=repo,
        session_id="sess1",
        current_message="Hello",
        session_metadata={},
        limit=10
    )

    assert len(context) == 1
    assert context[0]["role"] == "user"
    assert context[0]["content"] == "Hello"
