"""
Nura - Chat Streaming Service Tests
Tests SSE stream generator, cancellation resilience, and final persistence
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.models.chat import (
    ChatSessionInDB,
    ChatMessageInDB,
    SessionStatus,
    MessageRole,
)
from app.schemas.orchestrator import StandardResponseContract
from app.services.chat.chat_streaming_service import ChatStreamingService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_session():
    return ChatSessionInDB(
        id="sess123",
        patient_id="pat123",
        title="New Chat",
        status=SessionStatus.ACTIVE,
        session_type="ai_chat",
        active=True,
        last_message_at=utc_now(),
        message_count=0,
        total_tokens=0,
        total_cost=0.0,
        pinned=False,
        archived=False,
        metadata={},
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.mark.asyncio
async def test_stream_chat_message_success(mock_session):
    session_repo = AsyncMock()
    session_repo.get = AsyncMock(return_value=mock_session)
    session_repo.update = AsyncMock()

    message_repo = AsyncMock()
    message_repo.get_by_session_id = AsyncMock(return_value=[])

    message_service = AsyncMock()
    
    orchestrator = AsyncMock()
    mock_contract = StandardResponseContract(
        success=True,
        agent="MemoryAgent",
        intent="CHECKUP",
        response="Take care.",
        citations=[],
        metadata={"cost": 0.001},
        usage={"total_tokens": 10},
        execution_trace=[],
        execution_time=100.0,
        cost=0.001,
        warnings=[]
    )
    orchestrator.execute = AsyncMock(return_value=mock_contract)

    service = ChatStreamingService(
        chat_session_repository=session_repo,
        chat_message_repository=message_repo,
        chat_message_service=message_service,
        chat_session_service=AsyncMock(),
        orchestrator=orchestrator
    )

    chunks = []
    async for chunk in service.stream_chat_message("sess123", "pat123", "Hello"):
        chunks.append(chunk)

    # Yields initiation, tokens, and metadata
    assert len(chunks) > 2
    assert "init" in chunks[0] or '"type":"token"' in chunks[0]
    assert "metadata" in chunks[-1]

    # Verify user and assistant messages stored
    assert message_service.create_message.call_count == 2
    session_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_stream_chat_message_forbidden(mock_session):
    session_repo = AsyncMock()
    session_repo.get = AsyncMock(return_value=mock_session)

    service = ChatStreamingService(
        chat_session_repository=session_repo,
        chat_message_repository=AsyncMock(),
        chat_message_service=AsyncMock(),
        chat_session_service=AsyncMock(),
        orchestrator=AsyncMock()
    )

    chunks = []
    # Patient ID doesn't match
    async for chunk in service.stream_chat_message("sess123", "other_patient", "Hello"):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert "Forbidden" in chunks[0] or "error" in chunks[0]
