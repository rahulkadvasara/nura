"""
Nura - Chat Message Service Tests
Unit tests for ChatMessageService operations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.chat import (
    ChatMessageInDB,
    ChatSessionInDB,
    MessageRole,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageUpdate,
)
from app.services.chat_message_service import ChatMessageService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_patient():
    return UserInDB(
        id="507f1f77bcf86cd799439001",
        role=UserRole.PATIENT,
        email="patient@example.com",
        password_hash="hashed",
        full_name="Patient Test",
        phone="1234567890",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_session(sample_patient):
    return ChatSessionInDB(
        id="507f1f77bcf86cd799439080",
        patient_id=sample_patient.id,
        title="Checkup",
        description="General checkup",
        status="ACTIVE",
        session_type="ai_chat",
        active=True,
        last_message_at=utc_now(),
        message_count=0,
        total_tokens=0,
        total_cost=0.0,
        last_agent_used=None,
        pinned=False,
        archived=False,
        metadata={},
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_message_doc(sample_patient, sample_session):
    return {
        "_id": ObjectId("507f1f77bcf86cd799439090"),
        "session_id": sample_session.id,
        "patient_id": sample_patient.id,
        "role": "USER",
        "content": "Hello Nura",
        "citations": [],
        "attachments": [],
        "token_usage": {"prompt_tokens": 10},
        "latency_ms": 100,
        "metadata": {},
        "deleted": False,
        "created_at": utc_now(),
        "edited_at": None,
    }


class TestChatMessageService:
    @pytest.mark.asyncio
    async def test_create_message_success(self, sample_patient, sample_session, sample_message_doc):
        msg_repo = AsyncMock()
        msg_repo.collection = MagicMock()
        msg_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439090"))
        )
        msg_repo.collection.find_one = AsyncMock(return_value=sample_message_doc)

        sess_repo = AsyncMock()
        sess_repo.get = AsyncMock(return_value=sample_session)
        sess_repo.update = AsyncMock()

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_patient)

        service = ChatMessageService(msg_repo, sess_repo, user_repo)
        schema = ChatMessageCreate(
            session_id=sample_session.id,
            patient_id=sample_patient.id,
            role=MessageRole.USER,
            content="Hello Nura",
            token_usage={"prompt_tokens": 10},
            latency_ms=100,
        )

        result = await service.create_message(schema)
        assert isinstance(result, ChatMessageInDB)
        assert result.id == "507f1f77bcf86cd799439090"
        assert result.content == "Hello Nura"
        
        # Verify repositories were updated
        sess_repo.get.assert_called_once_with(sample_session.id)
        user_repo.get.assert_called_once_with(sample_patient.id)
        sess_repo.update.assert_called_once()  # Last message timestamp, count, tokens updated

    @pytest.mark.asyncio
    async def test_list_messages_by_session(self, sample_message_doc):
        msg_repo = AsyncMock()
        msg_repo.get_by_session_id = AsyncMock(return_value=[ChatMessageInDB.from_mongo(sample_message_doc)])
        sess_repo = AsyncMock()
        user_repo = AsyncMock()

        service = ChatMessageService(msg_repo, sess_repo, user_repo)
        results = await service.list_messages_by_session("507f1f77bcf86cd799439080", limit=10, skip=0)

        assert len(results) == 1
        assert results[0].content == "Hello Nura"
        msg_repo.get_by_session_id.assert_called_once_with("507f1f77bcf86cd799439080", limit=10, skip=0, include_deleted=False)

    @pytest.mark.asyncio
    async def test_update_message(self, sample_message_doc):
        msg_repo = AsyncMock()
        updated_doc = {**sample_message_doc, "content": "Updated Message", "edited_at": utc_now()}
        msg_repo.update = AsyncMock(return_value=ChatMessageInDB.from_mongo(updated_doc))
        sess_repo = AsyncMock()
        user_repo = AsyncMock()

        service = ChatMessageService(msg_repo, sess_repo, user_repo)
        schema = ChatMessageUpdate(content="Updated Message")
        result = await service.update_message("507f1f77bcf86cd799439090", schema)

        assert result is not None
        assert result.content == "Updated Message"
        assert result.edited_at is not None

    @pytest.mark.asyncio
    async def test_delete_message(self, sample_message_doc):
        msg_repo = AsyncMock()
        deleted_doc = {**sample_message_doc, "deleted": True}
        msg_repo.update = AsyncMock(return_value=ChatMessageInDB.from_mongo(deleted_doc))
        sess_repo = AsyncMock()
        user_repo = AsyncMock()

        service = ChatMessageService(msg_repo, sess_repo, user_repo)
        success = await service.delete_message("507f1f77bcf86cd799439090")

        assert success is True
        msg_repo.update.assert_called_once()
