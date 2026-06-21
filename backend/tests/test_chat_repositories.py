"""
Nura - Chat and Messaging Repositories Tests
Unit tests for ChatSessionRepository and ChatMessageRepository using mocked MongoDB collections.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionInDB,
    SessionType,
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageInDB,
    SenderType,
    MessageType,
)
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.chat_message_repository import ChatMessageRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_session_doc(
    session_id: str = "507f1f77bcf86cd799439080",
    patient_id: str = "507f1f77bcf86cd799439001",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(session_id),
        "patient_id": patient_id,
        "title": "General Chat",
        "session_type": "ai_chat",
        "active": True,
        "last_message_at": now,
        "created_at": now,
        "updated_at": now,
    }


def make_message_doc(
    message_id: str = "507f1f77bcf86cd799439090",
    session_id: str = "507f1f77bcf86cd799439080",
    sender_id: str = "507f1f77bcf86cd799439001",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(message_id),
        "session_id": session_id,
        "sender_type": "patient",
        "sender_id": sender_id,
        "message": "Hello doc",
        "message_type": "text",
        "metadata": {},
        "created_at": now,
    }


def make_mock_collection(find_one_return=None, find_return=None, update_result=None):
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)

    insert_result = MagicMock()
    insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439080")
    collection.insert_one = AsyncMock(return_value=insert_result)

    upd_result = MagicMock()
    upd_result.modified_count = 1 if update_result is None else update_result
    collection.update_one = AsyncMock(return_value=upd_result)

    del_result = MagicMock()
    del_result.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=del_result)

    cursor = MagicMock()
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.sort = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=find_return or [])
    collection.find = MagicMock(return_value=cursor)

    return collection


class TestChatSessionRepository:
    @pytest.mark.asyncio
    async def test_create_session(self):
        doc = make_session_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = ChatSessionRepository(collection)

        session_create = ChatSessionCreate(
            patient_id="507f1f77bcf86cd799439001",
            title="General Chat",
            session_type=SessionType.AI_CHAT,
        )
        result = await repo.create(session_create)
        assert isinstance(result, ChatSessionInDB)
        assert result.patient_id == "507f1f77bcf86cd799439001"
        assert result.title == "General Chat"

    @pytest.mark.asyncio
    async def test_get_session(self):
        doc = make_session_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = ChatSessionRepository(collection)

        result = await repo.get_by_id("507f1f77bcf86cd799439080")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439080"

    @pytest.mark.asyncio
    async def test_get_by_patient_id(self):
        docs = [make_session_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ChatSessionRepository(collection)

        results = await repo.get_by_patient_id("507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert results[0].patient_id == "507f1f77bcf86cd799439001"

    @pytest.mark.asyncio
    async def test_get_active_sessions(self):
        docs = [make_session_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ChatSessionRepository(collection)

        results = await repo.get_active_sessions(patient_id="507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert results[0].active is True

    @pytest.mark.asyncio
    async def test_update_session(self):
        updated_doc = make_session_doc()
        updated_doc["active"] = False
        collection = make_mock_collection(find_one_return=updated_doc)
        repo = ChatSessionRepository(collection)

        update = ChatSessionUpdate(active=False)
        result = await repo.update("507f1f77bcf86cd799439080", update)
        assert result is not None
        assert result.active is False

    @pytest.mark.asyncio
    async def test_delete_session(self):
        collection = make_mock_collection()
        repo = ChatSessionRepository(collection)
        result = await repo.delete("507f1f77bcf86cd799439080")
        assert result is True

    @pytest.mark.asyncio
    async def test_list_sessions(self):
        docs = [make_session_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ChatSessionRepository(collection)

        results = await repo.list()
        assert len(results) == 1


class TestChatMessageRepository:
    @pytest.mark.asyncio
    async def test_create_message(self):
        doc = make_message_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = ChatMessageRepository(collection)

        message_create = ChatMessageCreate(
            session_id="507f1f77bcf86cd799439080",
            sender_type=SenderType.PATIENT,
            sender_id="507f1f77bcf86cd799439001",
            message="Hello doc",
        )
        result = await repo.create(message_create)
        assert isinstance(result, ChatMessageInDB)
        assert result.session_id == "507f1f77bcf86cd799439080"
        assert result.message == "Hello doc"

    @pytest.mark.asyncio
    async def test_get_message(self):
        doc = make_message_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = ChatMessageRepository(collection)

        result = await repo.get_by_id("507f1f77bcf86cd799439090")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439090"

    @pytest.mark.asyncio
    async def test_get_by_session_id(self):
        docs = [make_message_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ChatMessageRepository(collection)

        results = await repo.get_by_session_id("507f1f77bcf86cd799439080")
        assert len(results) == 1
        assert results[0].session_id == "507f1f77bcf86cd799439080"

    @pytest.mark.asyncio
    async def test_get_latest_messages(self):
        docs = [make_message_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ChatMessageRepository(collection)

        results = await repo.get_latest_messages("507f1f77bcf86cd799439080", limit=10)
        assert len(results) == 1
        # The query should sort and collection.find was called
        collection.find.assert_called_once_with({"session_id": "507f1f77bcf86cd799439080"})
