"""
Nura - Chat and Messaging Schemas
Pydantic v2 schemas for chat API requests and responses, preparing for future AI layers
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.chat import (
    SessionType,
    SenderType,
    MessageType,
)


# ---------------------------------------------------------------------------
# Future AI & RAG Schema Design (Task 7 Preparation)
# ---------------------------------------------------------------------------

class ChatMessageMetadata(BaseModel):
    """Schema for chat message metadata supporting future AI, RAG, and Agent workflows."""
    model_config = ConfigDict(extra="allow")

    # Context retrieval / RAG
    context_chunks: Optional[List[Dict[str, Any]]] = Field(None, description="Qdrant search or context retrieval chunks")
    
    # Memory
    memory_summary: Optional[str] = Field(None, description="Short summary of memory used for context")
    
    # Citations
    citations: Optional[List[Dict[str, Any]]] = Field(None, description="References/citations to external medical documents or reports")
    
    # Report / Entity References
    referenced_report_ids: Optional[List[str]] = Field(None, description="List of report IDs referenced in this message")
    referenced_prescription_ids: Optional[List[str]] = Field(None, description="List of prescription IDs referenced in this message")
    referenced_appointment_ids: Optional[List[str]] = Field(None, description="List of appointment IDs referenced in this message")
    
    # Handoffs & Intent
    handoff: Optional[Dict[str, Any]] = Field(None, description="Agent handoff information (e.g. state handoff between agents)")
    routing_intent: Optional[str] = Field(None, description="Router agent detected intent")
    
    # Analytics
    sentiment: Optional[str] = Field(None, description="Sentiment analysis of user message")
    latency_ms: Optional[float] = Field(None, description="AI model response latency")
    tokens_used: Optional[Dict[str, int]] = Field(None, description="Token consumption metrics")


# ---------------------------------------------------------------------------
# Chat Session Schemas
# ---------------------------------------------------------------------------

class ChatSessionCreateSchema(BaseModel):
    """Request schema for creating a new chat session"""
    patient_id: str = Field(..., description="Reference to the patient user ID")
    title: str = Field(..., min_length=1, max_length=200, description="Title/topic of the chat session")
    session_type: SessionType = Field(..., description="Type of chat session")
    active: bool = Field(default=True, description="Whether the session is active")


class ChatSessionUpdateSchema(BaseModel):
    """Request schema for updating a chat session"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    active: Optional[bool] = None
    last_message_at: Optional[datetime] = None


class ChatSessionResponse(BaseModel):
    """Response schema for a chat session"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Session ID")
    patient_id: str = Field(..., description="Patient user ID")
    title: str = Field(..., description="Title/topic of the session")
    session_type: SessionType = Field(..., description="Session type")
    active: bool = Field(..., description="Active status")
    last_message_at: datetime = Field(..., description="Timestamp of last message")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Chat Message Schemas
# ---------------------------------------------------------------------------

class ChatMessageCreateSchema(BaseModel):
    """Request schema for creating a new chat message"""
    session_id: str = Field(..., description="Reference to the chat session ID")
    sender_type: SenderType = Field(..., description="Sender type")
    sender_id: str = Field(..., description="User ID of the sender")
    message: str = Field(..., min_length=1, max_length=5000, description="Message text content")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Type of message content")
    metadata: Optional[ChatMessageMetadata] = Field(default_factory=ChatMessageMetadata, description="Message metadata")


class ChatMessageUpdateSchema(BaseModel):
    """Request schema for updating an existing chat message"""
    message: Optional[str] = Field(None, min_length=1, max_length=5000)
    metadata: Optional[ChatMessageMetadata] = None


class ChatMessageResponse(BaseModel):
    """Response schema for a chat message"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Message ID")
    session_id: str = Field(..., description="Session ID")
    sender_type: SenderType = Field(..., description="Sender type")
    sender_id: str = Field(..., description="User ID of the sender")
    message: str = Field(..., description="Message text content")
    message_type: MessageType = Field(..., description="Type of message content")
    metadata: ChatMessageMetadata = Field(..., description="Message metadata")
    created_at: datetime = Field(..., description="Message creation timestamp")
