import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.chat.analytics_service import AnalyticsService


@pytest.mark.asyncio
async def test_analytics_aggregation():
    mock_session_repo = AsyncMock()
    mock_session_repo.get_many.return_value = [
        MagicMock(id="sess1"),
        MagicMock(id="sess2"),
        MagicMock(id="sess3")
    ]

    mock_message_repo = AsyncMock()
    mock_message_repo.get_many.return_value = [
        MagicMock(id="msg1"),
        MagicMock(id="msg2"),
        MagicMock(id="msg3"),
        MagicMock(id="msg4"),
        MagicMock(id="msg5"),
        MagicMock(id="msg6")
    ]

    service = AnalyticsService(session_repo=mock_session_repo, message_repo=mock_message_repo)
    analytics = await service.get_analytics()

    assert analytics["total_conversations"] == 3
    assert analytics["messages_per_day"] == 6
    assert analytics["average_conversation_length"] == 2.0
    assert "agent_usage" in analytics
    assert "rich_card_usage" in analytics
