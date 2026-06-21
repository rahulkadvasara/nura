"""
Nura - Chat and Messaging Models Tests
Tests for chat_sessions and chat_messages Pydantic models
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from app.models.chat import (
    SessionType,
    SenderType,
    MessageType,
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionInDB,
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageInDB,
)
from app.schemas.chat import ChatMessageMetadata


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TestChatEnums:
    def test_session_type_values(self):
        assert SessionType.AI_CHAT == "ai_chat"
        assert SessionType.DOCTOR_CHAT == "doctor_chat"
        assert SessionType.SUPPORT_CHAT == "support_chat"

    def test_sender_type_values(self):
        assert SenderType.PATIENT == "patient"
        assert SenderType.DOCTOR == "doctor"
        assert SenderType.AI == "ai"
        assert SenderType.SYSTEM == "system"

    def test_message_type_values(self):
        assert MessageType.TEXT == "text"
        assert MessageType.REPORT_REFERENCE == "report_reference"
        assert MessageType.PRESCRIPTION_REFERENCE == "prescription_reference"
        assert MessageType.APPOINTMENT_REFERENCE == "appointment_reference"
        assert MessageType.SYSTEM_EVENT == "system_event"


class TestChatSessionModel:
    def test_create_session(self):
        now = utc_now()
        session = ChatSessionCreate(
            patient_id="507f1f77bcf86cd799439001",
            title="General Checkup Chat",
            session_type=SessionType.AI_CHAT,
            active=True,
            last_message_at=now,
        )
        assert session.patient_id == "507f1f77bcf86cd799439001"
        assert session.title == "General Checkup Chat"
        assert session.session_type == SessionType.AI_CHAT
        assert session.active is True
        assert session.last_message_at == now

    def test_session_default_values(self):
        session = ChatSessionCreate(
            patient_id="patient_1",
            title="AI Session",
            session_type=SessionType.AI_CHAT,
        )
        assert session.active is True
        assert isinstance(session.last_message_at, datetime)

    def test_session_update_partial(self):
        update = ChatSessionUpdate(active=False, title="New Title")
        assert update.active is False
        assert update.title == "New Title"
        assert update.last_message_at is None

    def test_session_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "patient_id": ObjectId("507f1f77bcf86cd799439001"),
            "title": "Discussion",
            "session_type": "ai_chat",
            "active": True,
            "last_message_at": now,
            "created_at": now,
            "updated_at": now,
        }
        session = ChatSessionInDB.from_mongo(raw)
        assert session.id == "507f1f77bcf86cd799439080"
        assert session.patient_id == "507f1f77bcf86cd799439001"
        assert session.created_at == now


class TestChatMessageModel:
    def test_create_message(self):
        meta = ChatMessageMetadata(
            sentiment="neutral",
            latency_ms=120.5,
            tokens_used={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        )
        message = ChatMessageCreate(
            session_id="507f1f77bcf86cd799439080",
            sender_type=SenderType.AI,
            sender_id="ai_system",
            message="Hello patient!",
            message_type=MessageType.TEXT,
            metadata=meta.model_dump(),
        )
        assert message.session_id == "507f1f77bcf86cd799439080"
        assert message.sender_type == SenderType.AI
        assert message.message == "Hello patient!"
        assert message.message_type == MessageType.TEXT
        assert message.metadata["sentiment"] == "neutral"
        assert message.metadata["latency_ms"] == 120.5

    def test_message_default_values(self):
        message = ChatMessageCreate(
            session_id="session_1",
            sender_type=SenderType.PATIENT,
            sender_id="patient_1",
            message="Hello doc",
        )
        assert message.message_type == MessageType.TEXT
        assert message.metadata == {}

    def test_message_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "session_id": ObjectId("507f1f77bcf86cd799439080"),
            "sender_type": "patient",
            "sender_id": ObjectId("507f1f77bcf86cd799439001"),
            "message": "Hello",
            "message_type": "text",
            "metadata": {},
            "created_at": now,
        }
        message = ChatMessageInDB.from_mongo(raw)
        assert message.id == "507f1f77bcf86cd799439090"
        assert message.session_id == "507f1f77bcf86cd799439080"
        assert message.sender_id == "507f1f77bcf86cd799439001"
        assert message.created_at == now
