"""
Nura - Citation Service Tests
Tests formatting and mapping raw citations matching clinical records
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from app.models.chat import (
    ChatMessageInDB,
    MessageRole,
)
from app.services.chat.citation_service import CitationService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_get_message_citations_success():
    message_repo = AsyncMock()
    
    mock_citations = [
        {
            "document_id": "doc_cardio_1",
            "source": "cardio_report.pdf",
            "page_number": 3,
            "section": "Echocardiogram",
            "score": 0.88
        }
    ]
    message = ChatMessageInDB(
        id="msg123",
        session_id="sess123",
        patient_id="pat123",
        role=MessageRole.ASSISTANT,
        content="Diagnostics normal.",
        citations=mock_citations,
        attachments=[],
        token_usage={},
        deleted=False,
        created_at=utc_now()
    )
    message_repo.get = AsyncMock(return_value=message)

    service = CitationService(chat_message_repository=message_repo)

    citations = await service.get_message_citations("msg123", "pat123")

    assert len(citations) == 1
    assert citations[0].document == "doc_cardio_1"
    assert citations[0].source == "cardio_report.pdf"
    assert citations[0].page == 3
    assert citations[0].section == "Echocardiogram"
    assert citations[0].confidence == 0.88
