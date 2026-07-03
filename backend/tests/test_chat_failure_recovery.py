import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.chat.chat_execution_service import ChatExecutionService
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_execution_failure_recovery_rate_limiter():
    mock_session_repo = AsyncMock()
    mock_message_repo = AsyncMock()
    mock_message_service = AsyncMock()
    mock_session_service = MagicMock()
    mock_orchestrator = AsyncMock()

    service = ChatExecutionService(
        chat_session_repository=mock_session_repo,
        chat_message_repository=mock_message_repo,
        chat_message_service=mock_message_service,
        chat_session_service=mock_session_service,
        orchestrator=mock_orchestrator,
        context_resolver=MagicMock(),
        rich_card_service=MagicMock()
    )

    # Trigger rate limiting block
    from app.services.chat.rate_limiter import get_rate_limiter
    limiter = get_rate_limiter()
    limiter.max_requests = 0 # Block everything immediately

    try:
        with pytest.raises(HTTPException) as exc_info:
            await service.execute_chat_message("sess123", "pat123", "Hello")
        assert exc_info.value.status_code == 429
    finally:
        # Reset limit to normal
        limiter.max_requests = 10


@pytest.mark.asyncio
async def test_execution_failure_invalid_session():
    mock_session_repo = AsyncMock()
    # Return None indicating session does not exist
    mock_session_repo.get.return_value = None

    mock_message_repo = AsyncMock()
    mock_message_service = AsyncMock()
    mock_session_service = MagicMock()
    mock_orchestrator = AsyncMock()

    service = ChatExecutionService(
        chat_session_repository=mock_session_repo,
        chat_message_repository=mock_message_repo,
        chat_message_service=mock_message_service,
        chat_session_service=mock_session_service,
        orchestrator=mock_orchestrator,
        context_resolver=MagicMock(),
        rich_card_service=MagicMock()
    )

    with pytest.raises(ValueError) as exc_info:
        await service.execute_chat_message("sess_invalid", "pat123", "Hello")
    
    assert "does not exist" in str(exc_info.value)
