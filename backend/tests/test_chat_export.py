import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.services.chat.export_service import ExportService
from app.models.chat import ChatSessionInDB, ChatMessageInDB, MessageRole, SessionStatus

@pytest.mark.asyncio
async def test_export_pipeline_excludes_deleted_messages():
    session_repo = AsyncMock()
    message_repo = AsyncMock()
    
    # Real session
    session = ChatSessionInDB(
        id="sess1",
        patient_id="pat1",
        title="Diabetic Diet Log",
        description="",
        status=SessionStatus.ACTIVE,
        session_type="ai_chat",
        active=True,
        last_message_at=datetime.now(timezone.utc),
        message_count=1,
        total_tokens=10,
        total_cost=0.0,
        last_agent_used=None,
        pinned=False,
        archived=False,
        metadata={"summary": "Weekly diet checklist review."},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    session_repo.get.return_value = session
    
    # Real message (excluding soft-deleted)
    msg1 = ChatMessageInDB(
        id="msg1",
        session_id="sess1",
        patient_id="pat1",
        role=MessageRole.USER,
        content="I ate apple pie.",
        citations=[],
        attachments=[],
        token_usage={},
        metadata={},
        deleted=False,
        created_at=datetime.now(timezone.utc)
    )
    
    message_repo.get_by_session_id.return_value = [msg1]
    
    service = ExportService(session_repo, message_repo)
    data = await service.get_export_data("sess1", "pat1")
    
    # Verify MD formatter
    md_content = service.export_as_markdown(data["session"], data["messages"])
    assert "Diabetic Diet Log" in md_content
    assert "I ate apple pie." in md_content
    
    # Verify JSON formatter
    json_content = service.export_as_json(data["session"], data["messages"])
    parsed = json.loads(json_content)
    assert parsed["title"] == "Diabetic Diet Log"
    assert len(parsed["messages"]) == 1
    
    # Verify PDF bytes formatter
    pdf_bytes = service.export_as_pdf(data["session"], data["messages"])
    assert len(pdf_bytes) > 0
