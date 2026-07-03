"""
Nura - Conversation Evaluator Service Tests
Verifies worthiness scoring integration and telemetry registrations
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from app.models.chat import ChatMessageInDB, MessageRole
from app.services.chat_memory.conversation_evaluator import ConversationEvaluator
from app.services.chat_memory.telemetry import memory_telemetry


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_evaluate_session_success():
    # Mock message repository
    message_repo = AsyncMock()
    
    messages = [
        ChatMessageInDB(
            id="msg1",
            session_id="sess1",
            patient_id="pat1",
            role=MessageRole.USER,
            content="I am having chest pain.",
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
            content="Please schedule an appointment with a doctor immediately.",
            citations=[],
            attachments=[],
            token_usage={},
            deleted=False,
            created_at=utc_now()
        )
    ]
    message_repo.get_by_session_id = AsyncMock(return_value=messages)

    evaluator = ConversationEvaluator(chat_message_repository=message_repo)

    memory_telemetry.reset()
    res = await evaluator.evaluate_session("sess1")

    assert res["clinical_score"] > 0.0
    assert memory_telemetry.get_statistics()["evaluations_count"] == 1
