"""
Nura - Feedback Service Tests
Verifies rating inputs storage in decoupled collections
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.models.chat import (
    ChatMessageInDB,
    MessageRole,
)
from app.services.chat.feedback_service import FeedbackService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_submit_feedback_success():
    # Mock databases and collection
    db = MagicMock()
    mock_collection = AsyncMock()
    db.chat_feedbacks = mock_collection

    # Mock Message repo
    message_repo = AsyncMock()
    message = ChatMessageInDB(
        id="msg123",
        session_id="sess123",
        patient_id="pat123",
        role=MessageRole.ASSISTANT,
        content="Drink water",
        citations=[],
        attachments=[],
        token_usage={},
        deleted=False,
        created_at=utc_now()
    )
    message_repo.get = AsyncMock(return_value=message)

    service = FeedbackService(db=db, chat_message_repository=message_repo)

    result = await service.submit_feedback(
        message_id="msg123",
        patient_id="pat123",
        rating="helpful",
        comment="Nice answer!"
    )

    assert result is True
    # Verify feedback was inserted
    mock_collection.insert_one.assert_called_once()
    args, kwargs = mock_collection.insert_one.call_args
    inserted_doc = args[0]
    assert inserted_doc["message_id"] == "msg123"
    assert inserted_doc["rating"] == "helpful"
    assert inserted_doc["comment"] == "Nice answer!"


@pytest.mark.asyncio
async def test_submit_feedback_forbidden():
    message_repo = AsyncMock()
    message = ChatMessageInDB(
        id="msg123",
        session_id="sess123",
        patient_id="other_patient",  # Forbidden owner
        role=MessageRole.ASSISTANT,
        content="Drink water",
        citations=[],
        attachments=[],
        token_usage={},
        deleted=False,
        created_at=utc_now()
    )
    message_repo.get = AsyncMock(return_value=message)

    service = FeedbackService(db=MagicMock(), chat_message_repository=message_repo)

    with pytest.raises(PermissionError):
        await service.submit_feedback(
            message_id="msg123",
            patient_id="pat123",  # Accessing patient
            rating="helpful"
        )
