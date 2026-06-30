"""
Nura - Chat and Messaging Models
MongoDB models for chat_sessions and chat_messages collections
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SessionStatus(str, Enum):
    """Status of a chat session"""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class SessionType(str, Enum):
    """Supported types of chat sessions for backwards compatibility"""
    AI_CHAT = "ai_chat"
    DOCTOR_CHAT = "doctor_chat"
    SUPPORT_CHAT = "support_chat"


class MessageRole(str, Enum):
    """Role of the message creator"""
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


# Obsolete enums kept for compatibility
class SenderType(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    AI = "ai"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    SYSTEM_EVENT = "system_event"


# ---------------------------------------------------------------------------
# Chat Sessions
# ---------------------------------------------------------------------------

class ChatSessionBase(BaseModel):
    """Base fields shared by chat session models"""
    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(..., description="Reference to the patient user ID")
    title: str = Field(..., min_length=1, max_length=200, description="Title/topic of the chat session")
    description: Optional[str] = Field(default=None, description="Optional description of the session")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Status of the session")
    session_type: SessionType = Field(default=SessionType.AI_CHAT, description="Type of session (for compatibility)")
    active: bool = Field(default=True, description="Whether the session is currently active")
    last_message_at: datetime = Field(default_factory=utc_now, description="Timestamp of the last message in this session")
    message_count: int = Field(default=0, description="Count of messages in the session")
    total_tokens: int = Field(default=0, description="Total tokens used in this session")
    total_cost: float = Field(default=0.0, description="Total cost of the session")
    last_agent_used: Optional[str] = Field(default=None, description="Name of the last agent used")
    pinned: bool = Field(default=False, description="Whether the session is pinned")
    archived: bool = Field(default=False, description="Whether the session is archived")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata dictionary")


class ChatSessionCreate(ChatSessionBase):
    """Model used to create a new chat session record"""
    pass


class ChatSessionUpdate(BaseModel):
    """Model used to update an existing chat session record"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[SessionStatus] = None
    active: Optional[bool] = None
    last_message_at: Optional[datetime] = None
    message_count: Optional[int] = None
    total_tokens: Optional[int] = None
    total_cost: Optional[float] = None
    last_agent_used: Optional[str] = None
    pinned: Optional[bool] = None
    archived: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


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
        for field in ("patient_id",):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)


# ---------------------------------------------------------------------------
# Chat Messages
# ---------------------------------------------------------------------------

class ChatMessageBase(BaseModel):
    """Base fields shared by chat message models"""
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., description="Reference to the chat session ID")
    patient_id: str = Field(..., description="Reference to the patient user ID")
    role: MessageRole = Field(..., description="Role of the sender")
    content: str = Field(..., min_length=1, max_length=10000, description="Content of the message")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations used in the response")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Message attachments")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token consumption statistics")
    latency_ms: Optional[int] = Field(default=None, description="Response generation latency in ms")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")
    deleted: bool = Field(default=False, description="Whether the message is soft deleted")


class ChatMessageCreate(ChatMessageBase):
    """Model used to create a new chat message record"""
    pass


class ChatMessageUpdate(BaseModel):
    """Model used to update an existing chat message record"""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    edited_at: Optional[datetime] = None
    deleted: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageInDB(ChatMessageBase):
    """Chat message as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Message creation timestamp")
    edited_at: Optional[datetime] = Field(default=None, description="Message edit timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "ChatMessageInDB":
        """Create ChatMessageInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("session_id", "patient_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)
