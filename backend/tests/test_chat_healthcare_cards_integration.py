import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.models.chat import ChatSessionInDB, ChatMessageInDB, SessionStatus, MessageRole
from app.schemas.orchestrator import StandardResponseContract
from app.schemas.chat import ChatExecutionResponse, RichCardResponse, RichCardAction
from app.services.chat.chat_execution_service import ChatExecutionService
from app.services.chat.chat_streaming_service import ChatStreamingService


@pytest.fixture
def mock_session():
    return ChatSessionInDB(
        id="sess123",
        patient_id="pat123",
        title="Session",
        description="Description",
        status=SessionStatus.ACTIVE,
        session_type="ai_chat",
        active=True,
        last_message_at=datetime.now(timezone.utc),
        message_count=0,
        total_tokens=0,
        total_cost=0.0,
        pinned=False,
        archived=False,
        metadata={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_user_message():
    return ChatMessageInDB(
        id="msg123",
        session_id="sess123",
        patient_id="pat123",
        role=MessageRole.USER,
        content="Check my blood test report",
        citations=[],
        attachments=[],
        token_usage={},
        deleted=False,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_assistant_message():
    return ChatMessageInDB(
        id="msg456",
        session_id="sess123",
        patient_id="pat123",
        role=MessageRole.ASSISTANT,
        content="Here is your report analysis.",
        citations=[],
        attachments=[],
        token_usage={"total_tokens": 100},
        latency_ms=200,
        deleted=False,
        metadata={},
        created_at=datetime.now(timezone.utc)
    )


@pytest.mark.asyncio
async def test_execution_service_attaches_cards(mock_session, mock_user_message, mock_assistant_message):
    session_repo = AsyncMock()
    session_repo.get.return_value = mock_session
    session_repo.update = AsyncMock()

    message_repo = AsyncMock()
    message_repo.get_by_session_id.return_value = []

    message_service = AsyncMock()
    message_service.create_message.side_effect = [mock_user_message, mock_assistant_message]

    orchestrator = AsyncMock()
    orchestrator.execute.return_value = StandardResponseContract(
        success=True,
        agent="ReportAgent",
        intent="REPORT_ANALYSIS",
        response="Here is your report analysis.",
        citations=[],
        metadata={"cost": 0.005},
        usage={"total_tokens": 100},
        execution_trace=[],
        execution_time=200.0,
        cost=0.005,
        warnings=[]
    )

    # Mock Resolver & Card Service
    context_resolver = AsyncMock()
    context_resolver.resolve_context.return_value = {"reports": [AsyncMock(id="rep1", document_type="Blood Report")]}

    rich_card_service = MagicMock()
    dummy_card = RichCardResponse(
        card_type="report",
        title="Blood Report Card",
        icon="FileText",
        status="normal",
        summary="Your cholesterol levels are normal.",
        metadata={"report_id": "rep1"},
        actions=[
            RichCardAction(action_type="OPEN_REPORT", label="Open", url="/dashboard/records/rep1")
        ]
    )
    rich_card_service.build_cards.return_value = [dummy_card]

    service = ChatExecutionService(
        chat_session_repository=session_repo,
        chat_message_repository=message_repo,
        chat_message_service=message_service,
        chat_session_service=AsyncMock(),
        orchestrator=orchestrator,
        context_resolver=context_resolver,
        rich_card_service=rich_card_service
    )

    response = await service.execute_chat_message(
        session_id="sess123",
        patient_id="pat123",
        message="Check my blood test report"
    )

    assert isinstance(response, ChatExecutionResponse)
    assert len(response.cards) == 1
    assert response.cards[0].title == "Blood Report Card"
    assert response.cards[0].card_type == "report"
    assert len(response.actions) == 1
    assert response.actions[0].action_type == "OPEN_REPORT"

    # Verify context_resolver was invoked
    context_resolver.resolve_context.assert_called_once_with("pat123", "Check my blood test report")


@pytest.mark.asyncio
async def test_streaming_service_attaches_cards(mock_session, mock_user_message, mock_assistant_message):
    session_repo = AsyncMock()
    session_repo.get.return_value = mock_session
    session_repo.update = AsyncMock()

    message_repo = AsyncMock()
    message_repo.get_by_session_id.return_value = []

    message_service = AsyncMock()
    message_service.create_message.side_effect = [mock_user_message, mock_assistant_message]

    orchestrator = AsyncMock()
    orchestrator.execute.return_value = StandardResponseContract(
        success=True,
        agent="ReportAgent",
        intent="REPORT_ANALYSIS",
        response="Here is your report analysis.",
        citations=[],
        metadata={"cost": 0.005},
        usage={"total_tokens": 100},
        execution_trace=[],
        execution_time=200.0,
        cost=0.005,
        warnings=[]
    )

    context_resolver = AsyncMock()
    context_resolver.resolve_context.return_value = {"reports": [AsyncMock(id="rep1", document_type="Blood Report")]}

    rich_card_service = MagicMock()
    dummy_card = RichCardResponse(
        card_type="report",
        title="Blood Report Card",
        icon="FileText",
        status="normal",
        summary="Your cholesterol levels are normal.",
        metadata={"report_id": "rep1"},
        actions=[
            RichCardAction(action_type="OPEN_REPORT", label="Open", url="/dashboard/records/rep1")
        ]
    )
    rich_card_service.build_cards.return_value = [dummy_card]

    streaming_service = ChatStreamingService(
        chat_session_repository=session_repo,
        chat_message_repository=message_repo,
        chat_message_service=message_service,
        chat_session_service=AsyncMock(),
        orchestrator=orchestrator,
        context_resolver=context_resolver,
        rich_card_service=rich_card_service
    )

    chunks = []
    async for chunk in streaming_service.stream_chat_message(
        session_id="sess123",
        patient_id="pat123",
        message="Check my blood test report"
    ):
        chunks.append(chunk)

    # Find the metadata chunk
    metadata_chunk = None
    for c in chunks:
        if "data: " in c:
            data_dict = json.loads(c.replace("data: ", "").strip())
            if data_dict.get("type") == "metadata":
                metadata_chunk = data_dict
                break

    assert metadata_chunk is not None
    assert "cards" in metadata_chunk
    assert len(metadata_chunk["cards"]) == 1
    assert metadata_chunk["cards"][0]["title"] == "Blood Report Card"
    assert len(metadata_chunk["actions"]) == 1
    assert metadata_chunk["actions"][0]["action_type"] == "OPEN_REPORT"
