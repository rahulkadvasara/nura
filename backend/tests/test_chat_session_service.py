"""
Nura - Chat Session Service Tests
Unit tests for ChatSessionService lifecycle operations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.chat import (
    ChatSessionInDB,
    SessionType,
    SessionStatus,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
)
from app.services.chat_session_service import ChatSessionService


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
def sample_session_doc(sample_patient):
    now = utc_now()
    return {
        "_id": ObjectId("507f1f77bcf86cd799439080"),
        "patient_id": sample_patient.id,
        "title": "Checkup",
        "description": "General checkup",
        "status": "ACTIVE",
        "session_type": "ai_chat",
        "active": True,
        "last_message_at": now,
        "message_count": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "last_agent_used": None,
        "pinned": False,
        "archived": False,
        "metadata": {},
        "created_at": now,
        "updated_at": now,
    }


class TestChatSessionService:
    @pytest.mark.asyncio
    async def test_create_session_success(self, sample_patient, sample_session_doc):
        sess_repo = AsyncMock()
        sess_repo.collection = MagicMock()
        sess_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439080"))
        )
        sess_repo.collection.find_one = AsyncMock(return_value=sample_session_doc)

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_patient)

        service = ChatSessionService(sess_repo, user_repo)
        schema = ChatSessionCreate(
            patient_id=sample_patient.id,
            title="Checkup",
            description="General checkup",
        )

        result = await service.create_session(schema)
        assert isinstance(result, ChatSessionInDB)
        assert result.id == "507f1f77bcf86cd799439080"
        assert result.status == SessionStatus.ACTIVE
        user_repo.get.assert_called_once_with(sample_patient.id)

    @pytest.mark.asyncio
    async def test_rename_session(self, sample_session_doc):
        sess_repo = AsyncMock()
        renamed_doc = {**sample_session_doc, "title": "New Title"}
        sess_repo.update = AsyncMock(return_value=ChatSessionInDB.from_mongo(renamed_doc))
        user_repo = AsyncMock()

        service = ChatSessionService(sess_repo, user_repo)
        result = await service.rename_session("507f1f77bcf86cd799439080", "New Title")
        
        assert result is not None
        assert result.title == "New Title"
        sess_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_pin_session(self, sample_session_doc):
        sess_repo = AsyncMock()
        pinned_doc = {**sample_session_doc, "pinned": True}
        sess_repo.update = AsyncMock(return_value=ChatSessionInDB.from_mongo(pinned_doc))
        user_repo = AsyncMock()

        service = ChatSessionService(sess_repo, user_repo)
        result = await service.pin_session("507f1f77bcf86cd799439080", True)

        assert result is not None
        assert result.pinned is True

    @pytest.mark.asyncio
    async def test_archive_session(self, sample_session_doc):
        sess_repo = AsyncMock()
        archived_doc = {
            **sample_session_doc,
            "archived": True,
            "status": "ARCHIVED",
            "active": False
        }
        sess_repo.update = AsyncMock(return_value=ChatSessionInDB.from_mongo(archived_doc))
        user_repo = AsyncMock()

        service = ChatSessionService(sess_repo, user_repo)
        result = await service.archive_session("507f1f77bcf86cd799439080", True)

        assert result is not None
        assert result.archived is True
        assert result.status == SessionStatus.ARCHIVED
        assert result.active is False

    @pytest.mark.asyncio
    async def test_delete_session(self, sample_session_doc):
        sess_repo = AsyncMock()
        deleted_doc = {
            **sample_session_doc,
            "status": "DELETED",
            "active": False
        }
        sess_repo.update = AsyncMock(return_value=ChatSessionInDB.from_mongo(deleted_doc))
        user_repo = AsyncMock()

        service = ChatSessionService(sess_repo, user_repo)
        success = await service.delete_session("507f1f77bcf86cd799439080")

        assert success is True

    @pytest.mark.asyncio
    async def test_restore_session(self, sample_session_doc):
        sess_repo = AsyncMock()
        active_doc = {
            **sample_session_doc,
            "status": "ACTIVE",
            "active": True
        }
        sess_repo.update = AsyncMock(return_value=ChatSessionInDB.from_mongo(active_doc))
        user_repo = AsyncMock()

        service = ChatSessionService(sess_repo, user_repo)
        result = await service.restore_session("507f1f77bcf86cd799439080")

        assert result is not None
        assert result.status == SessionStatus.ACTIVE
        assert result.active is True
