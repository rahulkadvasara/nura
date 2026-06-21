"""
Nura - Chat and Messaging Models
MongoDB models for chat_sessions and chat_messages collections
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SessionType(str, Enum):
    """Supported types of chat sessions"""
    AI_CHAT = "ai_chat"
    DOCTOR_CHAT = "doctor_chat"
    SUPPORT_CHAT = "support_chat"


class SenderType(str, Enum):
    """Types of participants sending messages"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    AI = "ai"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Types of content format in a message"""
    TEXT = "text"
    REPORT_REFERENCE = "report_reference"
    PRESCRIPTION_REFERENCE = "prescription_reference"
    APPOINTMENT_REFERENCE = "appointment_reference"
    SYSTEM_EVENT = "system_event"


# ---------------------------------------------------------------------------
# Chat Sessions
# ---------------------------------------------------------------------------

class ChatSessionBase(BaseModel):
    """Base fields shared by chat session models"""
    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(..., description="Reference to the patient user ID")
    title: str = Field(..., min_length=1, max_length=200, description="Title/topic of the chat session")
    session_type: SessionType = Field(..., description="Type of chat session")
    active: bool = Field(default=True, description="Whether the session is currently active")
    last_message_at: datetime = Field(default_factory=utc_now, description="Timestamp of the last message in this session")


class ChatSessionCreate(ChatSessionBase):
    """Model used to create a new chat session record"""
    pass


class ChatSessionUpdate(BaseModel):
    """Model used to update an existing chat session record"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    active: Optional[bool] = None
    last_message_at: Optional[datetime] = None


class ChatSessionInDB(ChatSessionBase):
    """Chat session as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "ChatSessionInDB":
        """Create ChatSessionInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        if "patient_id" in doc and doc["patient_id"] is not None and not isinstance(doc["patient_id"], str):
            doc["patient_id"] = str(doc["patient_id"])
        return cls(**doc)


# ---------------------------------------------------------------------------
# Chat Messages
# ---------------------------------------------------------------------------

class ChatMessageBase(BaseModel):
    """Base fields shared by chat message models"""
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., description="Reference to the chat session ID")
    sender_type: SenderType = Field(..., description="Sender type")
    sender_id: str = Field(..., description="User ID of the sender")
    message: str = Field(..., min_length=1, max_length=5000, description="Text content of the message")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Type of message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible dictionary for memory, context, citations, and agent handoffs")


class ChatMessageCreate(ChatMessageBase):
    """Model used to create a new chat message record"""
    pass


class ChatMessageUpdate(BaseModel):
    """Model used to update an existing chat message record"""
    message: Optional[str] = Field(None, min_length=1, max_length=5000)
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageInDB(ChatMessageBase):
    """Chat message as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Message creation timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "ChatMessageInDB":
        """Create ChatMessageInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("session_id", "sender_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)
