"""
Nura - Chat Execution Service Tests
Unit tests for ChatExecutionService AI orchestration and persistence logic
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.chat import (
    ChatSessionInDB,
    ChatMessageInDB,
    SessionStatus,
    MessageRole,
)
from app.schemas.orchestrator import StandardResponseContract
from app.schemas.chat import ChatExecutionResponse
from app.services.chat.chat_execution_service import ChatExecutionService
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_session():
    return ChatSessionInDB(
        id="sess123",
        patient_id="pat123",
        title="Flu session",
        description="Cold & flu query",
        status=SessionStatus.ACTIVE,
        session_type="ai_chat",
        active=True,
        last_message_at=utc_now(),
        message_count=2,
        total_tokens=100,
        total_cost=0.01,
        last_agent_used="MemoryAgent",
        pinned=False,
        archived=False,
        metadata={},
        created_at=utc_now(),
        updated_at=utc_now()
    )


@pytest.fixture
def mock_user_message():
    return ChatMessageInDB(
        id="msg123",
        session_id="sess123",
        patient_id="pat123",
        role=MessageRole.USER,
        content="I feel sick",
        citations=[],
        attachments=[],
        token_usage={},
        deleted=False,
        created_at=utc_now()
    )


@pytest.fixture
def mock_assistant_message():
    return ChatMessageInDB(
        id="msg456",
        session_id="sess123",
        patient_id="pat123",
        role=MessageRole.ASSISTANT,
        content="Drink water",
        citations=[],
        attachments=[],
        token_usage={"total_tokens": 50},
        latency_ms=500,
        deleted=False,
        created_at=utc_now()
    )


@pytest.mark.asyncio
async def test_execute_chat_message_success(mock_session, mock_user_message, mock_assistant_message):
    session_repo = AsyncMock()
    session_repo.get = AsyncMock(return_value=mock_session)
    session_repo.update = AsyncMock()

    message_repo = AsyncMock()
    # Mock context builder returning empty list for simplicity
    message_repo.get_by_session_id = AsyncMock(return_value=[])

    message_service = AsyncMock()
    message_service.create_message = AsyncMock(side_effect=[mock_user_message, mock_assistant_message])

    session_service = AsyncMock()

    orchestrator = AsyncMock()
    mock_contract = StandardResponseContract(
        success=True,
        agent="SymptomAgent",
        intent="SYMPTOM_CHECK",
        response="Drink water",
        citations=[],
        metadata={"cost": 0.002},
        usage={"total_tokens": 50},
        execution_trace=[],
        execution_time=500.0,
        cost=0.002,
        warnings=[]
    )
    orchestrator.execute = AsyncMock(return_value=mock_contract)

    service = ChatExecutionService(
        chat_session_repository=session_repo,
        chat_message_repository=message_repo,
        chat_message_service=message_service,
        chat_session_service=session_service,
        orchestrator=orchestrator
    )

    response = await service.execute_chat_message(
        session_id="sess123",
        patient_id="pat123",
        message="I feel sick"
    )

    assert isinstance(response, ChatExecutionResponse)
    assert response.assistant_message == "Drink water"
    assert response.agent_used == "SymptomAgent"
    assert response.cost == 0.002

    # Verify user message was stored
    assert message_service.create_message.call_count == 2
    # Verify session stats updated with new cost
    session_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_execute_chat_message_forbidden():
    session_repo = AsyncMock()
    # Session belongs to different patient
    other_session = ChatSessionInDB(
        id="sess123",
        patient_id="other_patient",
        title="Flu",
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
        updated_at=utc_now()
    )
    session_repo.get = AsyncMock(return_value=other_session)

    service = ChatExecutionService(
        chat_session_repository=session_repo,
        chat_message_repository=AsyncMock(),
        chat_message_service=AsyncMock(),
        chat_session_service=AsyncMock(),
        orchestrator=AsyncMock()
    )

    with pytest.raises(PermissionError):
        await service.execute_chat_message(
            session_id="sess123",
            patient_id="pat123",
            message="Hey"
        )


@pytest.mark.asyncio
async def test_execute_chat_message_orchestrator_failure(mock_session, mock_user_message):
    session_repo = AsyncMock()
    session_repo.get = AsyncMock(return_value=mock_session)

    message_repo = AsyncMock()
    message_repo.get_by_session_id = AsyncMock(return_value=[])

    message_service = AsyncMock()
    message_service.create_message = AsyncMock(return_value=mock_user_message)

    orchestrator = AsyncMock()
    # Orchestrator returns failure
    mock_contract = StandardResponseContract(
        success=False,
        agent=None,
        intent="ERROR",
        response="Service Unavailable",
        citations=[],
        metadata={"error": "Groq timeout"},
        usage={},
        execution_trace=[],
        execution_time=2000.0,
        cost=0.0,
        warnings=[]
    )
    orchestrator.execute = AsyncMock(return_value=mock_contract)

    service = ChatExecutionService(
        chat_session_repository=session_repo,
        chat_message_repository=message_repo,
        chat_message_service=message_service,
        chat_session_service=AsyncMock(),
        orchestrator=orchestrator
    )

    # Calling should raise RuntimeError but preserve user message storage call
    with pytest.raises(RuntimeError, match="Service Unavailable"):
        await service.execute_chat_message(
            session_id="sess123",
            patient_id="pat123",
            message="I feel sick"
        )

    # User message created
    message_service.create_message.assert_called_once()
