"""
Nura - Response Regeneration Service Tests
Verifies response regeneration logic, stats offsets, and message replacements
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.models.chat import (
    ChatSessionInDB,
    ChatMessageInDB,
    SessionStatus,
    MessageRole,
)
from app.schemas.orchestrator import StandardResponseContract
from app.schemas.chat import ChatExecutionResponse
from app.services.chat.regeneration_service import RegenerationService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_session():
    return ChatSessionInDB(
        id="sess123",
        patient_id="pat123",
        title="Checkup",
        status=SessionStatus.ACTIVE,
        session_type="ai_chat",
        active=True,
        last_message_at=utc_now(),
        message_count=2,
        total_tokens=100,
        total_cost=0.01,
        pinned=False,
        archived=False,
        metadata={},
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def mock_messages():
    return [
        ChatMessageInDB(
            id="msg_user",
            session_id="sess123",
            patient_id="pat123",
            role=MessageRole.USER,
            content="Check my throat",
            citations=[],
            attachments=[],
            token_usage={},
            deleted=False,
            created_at=utc_now()
        ),
        ChatMessageInDB(
            id="msg_assistant",
            session_id="sess123",
            patient_id="pat123",
            role=MessageRole.ASSISTANT,
            content="It looks red.",
            citations=[],
            attachments=[],
            token_usage={"total_tokens": 40},
            deleted=False,
            created_at=utc_now(),
            metadata={"cost": 0.002}
        )
    ]


@pytest.mark.asyncio
async def test_regenerate_latest_response_success(mock_session, mock_messages):
    session_repo = AsyncMock()
    session_repo.get = AsyncMock(return_value=mock_session)
    session_repo.update = AsyncMock()

    message_repo = AsyncMock()
    message_repo.get_by_session_id = AsyncMock(return_value=mock_messages)

    message_service = AsyncMock()
    message_service.delete_message = AsyncMock()
    
    mock_new_assistant_msg = ChatMessageInDB(
        id="msg_new_assistant",
        session_id="sess123",
        patient_id="pat123",
        role=MessageRole.ASSISTANT,
        content="Drink warm fluids.",
        citations=[],
        attachments=[],
        token_usage={"total_tokens": 50},
        deleted=False,
        created_at=utc_now()
    )
    message_service.create_message = AsyncMock(return_value=mock_new_assistant_msg)

    orchestrator = AsyncMock()
    mock_contract = StandardResponseContract(
        success=True,
        agent="SymptomAgent",
        intent="SYMPTOMS",
        response="Drink warm fluids.",
        citations=[],
        metadata={"cost": 0.003},
        usage={"total_tokens": 50},
        execution_trace=[],
        execution_time=200.0,
        cost=0.003,
        warnings=[]
    )
    orchestrator.execute = AsyncMock(return_value=mock_contract)

    service = RegenerationService(
        chat_session_repository=session_repo,
        chat_message_repository=message_repo,
        chat_message_service=message_service,
        orchestrator=orchestrator
    )

    response = await service.regenerate_latest_response("sess123", "pat123")

    assert isinstance(response, ChatExecutionResponse)
    assert response.assistant_message == "Drink warm fluids."
    assert response.agent_used == "SymptomAgent"
    assert response.cost == 0.003

    # Verifies soft deletion of old message
    message_service.delete_message.assert_called_once_with("msg_assistant")
    
    # Verifies session updates are offset and updated
    assert session_repo.update.call_count == 2
