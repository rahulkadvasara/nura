import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_current_user
from app.models.user import UserInDB, UserRole
from app.schemas.chat import ConversationSearchResponse, BookmarkResponse

from datetime import datetime, timezone

# Setup mock user auth dependency
mock_user = UserInDB(
    id="pat1",
    email="patient@test.com",
    full_name="Test Patient",
    password_hash="somehash",
    role=UserRole.PATIENT,
    is_active=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc)
)

@pytest.fixture
def client():
    # Bypass auth
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Mock MongoDB connection to prevent runtime errors
    from app.db.mongodb import mongodb_connection
    mongodb_connection.database = MagicMock()
    
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_search_conversations_api(client):
    search_service = AsyncMock()
    search_service.search_conversations.return_value = ConversationSearchResponse(results=[])
    
    from app.core.dependencies import get_conversation_search_service
    app.dependency_overrides[get_conversation_search_service] = lambda: search_service
    
    res = client.get("/api/v1/chat/search?query=chest")
    assert res.status_code == 200
    assert res.json()["success"] is True

def test_bookmark_message_api(client):
    bookmark_service = AsyncMock()
    
    from datetime import datetime, timezone
    bm_res = BookmarkResponse(
        id="bm1",
        message_id="msg1",
        session_id="sess1",
        patient_id="pat1",
        bookmarked_at=datetime.now(timezone.utc),
        message_content="Sample content",
        message_role="ASSISTANT"
    )
    bookmark_service.add_bookmark.return_value = bm_res
    
    from app.core.dependencies import get_bookmark_service
    app.dependency_overrides[get_bookmark_service] = lambda: bookmark_service
    
    res = client.post("/api/v1/chat/bookmark", json={"message_id": "msg1"})
    assert res.status_code == 200
    assert res.json()["data"]["id"] == "bm1"

def test_remove_bookmark_api(client):
    bookmark_service = AsyncMock()
    bookmark_service.remove_bookmark.return_value = True
    
    from app.core.dependencies import get_bookmark_service
    app.dependency_overrides[get_bookmark_service] = lambda: bookmark_service
    
    res = client.delete("/api/v1/chat/bookmark/msg1")
    assert res.status_code == 200
    assert res.json()["data"]["deleted"] is True
