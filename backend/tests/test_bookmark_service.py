import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.services.chat.bookmark_service import BookmarkService
from app.models.bookmark import BookmarkInDB
from app.models.chat import ChatMessageInDB, MessageRole

@pytest.mark.asyncio
async def test_add_bookmark_success():
    bookmark_repo = AsyncMock()
    message_repo = AsyncMock()
    session_repo = AsyncMock()
    
    bookmark_repo.get_by_user_and_message.return_value = None
    
    # Real message
    msg = ChatMessageInDB(
        id="msg1",
        session_id="sess1",
        patient_id="pat1",
        role=MessageRole.ASSISTANT,
        content="Clinical content",
        citations=[],
        attachments=[],
        token_usage={},
        metadata={},
        deleted=False,
        created_at=datetime.now(timezone.utc)
    )
    message_repo.get.return_value = msg
    
    # Real created bookmark
    created_bm = BookmarkInDB(
        id="bm1",
        message_id="msg1",
        session_id="sess1",
        patient_id="pat1",
        bookmarked_at=datetime.now(timezone.utc)
    )
    bookmark_repo.create.return_value = created_bm
    
    service = BookmarkService(bookmark_repo, message_repo, session_repo)
    res = await service.add_bookmark("pat1", "msg1")
    
    assert res.id == "bm1"
    assert res.message_content == "Clinical content"
    bookmark_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_add_bookmark_unauthorized():
    bookmark_repo = AsyncMock()
    message_repo = AsyncMock()
    session_repo = AsyncMock()
    
    msg = ChatMessageInDB(
        id="msg1",
        session_id="sess1",
        patient_id="different_pat",
        role=MessageRole.USER,
        content="Hello",
        citations=[],
        attachments=[],
        token_usage={},
        metadata={},
        deleted=False,
        created_at=datetime.now(timezone.utc)
    )
    message_repo.get.return_value = msg
    
    service = BookmarkService(bookmark_repo, message_repo, session_repo)
    with pytest.raises(PermissionError):
        await service.add_bookmark("pat1", "msg1")

@pytest.mark.asyncio
async def test_list_bookmarks_excludes_deleted_messages():
    bookmark_repo = AsyncMock()
    message_repo = AsyncMock()
    session_repo = AsyncMock()
    
    bm1 = BookmarkInDB(
        id="bm1",
        message_id="msg1",
        session_id="sess1",
        patient_id="pat1",
        bookmarked_at=datetime.now(timezone.utc)
    )
    
    bm2 = BookmarkInDB(
        id="bm2",
        message_id="msg2",
        session_id="sess1",
        patient_id="pat1",
        bookmarked_at=datetime.now(timezone.utc)
    )
    
    bookmark_repo.list_by_patient_id.return_value = [bm1, bm2]
    
    msg1 = ChatMessageInDB(
        id="msg1",
        session_id="sess1",
        patient_id="pat1",
        role=MessageRole.USER,
        content="Active user prompt",
        citations=[],
        attachments=[],
        token_usage={},
        metadata={},
        deleted=False,
        created_at=datetime.now(timezone.utc)
    )
    
    msg2 = ChatMessageInDB(
        id="msg2",
        session_id="sess1",
        patient_id="pat1",
        role=MessageRole.ASSISTANT,
        content="Deleted assistant reply",
        citations=[],
        attachments=[],
        token_usage={},
        metadata={},
        deleted=True,
        created_at=datetime.now(timezone.utc)
    )
    
    def mock_get(msg_id):
        if msg_id == "msg1":
            return msg1
        return msg2
        
    message_repo.get.side_effect = mock_get
    
    service = BookmarkService(bookmark_repo, message_repo, session_repo)
    bookmarks = await service.get_bookmarks("pat1")
    
    assert len(bookmarks) == 1
    assert bookmarks[0].message_id == "msg1"
    assert bookmarks[0].message_content == "Active user prompt"
