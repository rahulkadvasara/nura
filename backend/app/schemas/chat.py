"""
Nura - Chat and Messaging Schemas
Pydantic v2 schemas for chat API requests and responses
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.chat import (
    SessionType,
    SessionStatus,
    MessageRole,
)


# ---------------------------------------------------------------------------
# Chat Message Metadata Schema
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

class ChatSessionCreate(BaseModel):
    """Request schema for creating a new chat session"""
    patient_id: str = Field(..., description="Reference to the patient user ID")
    title: str = Field(..., min_length=1, max_length=200, description="Title/topic of the chat session")
    description: Optional[str] = Field(None, description="Optional description of the session")
    session_type: Optional[SessionType] = Field(SessionType.AI_CHAT, description="Type of session")


class ChatSessionUpdate(BaseModel):
    """Request schema for updating a chat session"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Optional description")
    pinned: Optional[bool] = Field(None, description="Pin state")
    archived: Optional[bool] = Field(None, description="Archive state")
    status: Optional[SessionStatus] = Field(None, description="Session status")


class ChatSessionResponse(BaseModel):
    """Response schema for a chat session"""
    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Session ID")
    patient_id: str = Field(..., description="Patient user ID")
    title: str = Field(..., description="Title/topic of the session")
    description: Optional[str] = Field(None, description="Description of the session")
    status: SessionStatus = Field(..., description="Status of the session")
    session_type: SessionType = Field(..., description="Session type")
    active: bool = Field(..., description="Active status")
    last_message_at: datetime = Field(..., description="Timestamp of last message")
    message_count: int = Field(..., description="Number of messages in session")
    total_tokens: int = Field(..., description="Total tokens consumed")
    total_cost: float = Field(..., description="Total cost of API execution")
    last_agent_used: Optional[str] = Field(None, description="Last AI agent used")
    pinned: bool = Field(..., description="Pin status")
    archived: bool = Field(..., description="Archive status")
    metadata: Dict[str, Any] = Field(..., description="Session metadata")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Chat Message Schemas
# ---------------------------------------------------------------------------

class ChatMessageCreate(BaseModel):
    """Request schema for creating a new chat message"""
    session_id: str = Field(..., description="Reference to the chat session ID")
    patient_id: str = Field(..., description="Reference to the patient user ID")
    role: MessageRole = Field(..., description="Role of the message author")
    content: str = Field(..., min_length=1, max_length=10000, description="Message text content")
    citations: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Citations used in response")
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Attachments")
    token_usage: Optional[Dict[str, int]] = Field(default_factory=dict, description="Token consumption metrics")
    latency_ms: Optional[int] = Field(None, description="Latency in ms")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Message metadata")


class ChatMessageUpdate(BaseModel):
    """Request schema for updating an existing chat message"""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    """Response schema for a chat message"""
    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Message ID")
    session_id: str = Field(..., description="Session ID")
    patient_id: str = Field(..., description="Patient user ID")
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    citations: List[Dict[str, Any]] = Field(..., description="References or citations")
    attachments: List[Dict[str, Any]] = Field(..., description="Attached items")
    token_usage: Dict[str, int] = Field(..., description="Tokens consumed")
    latency_ms: Optional[int] = Field(None, description="Response generation latency in ms")
    metadata: Dict[str, Any] = Field(..., description="Message metadata")
    created_at: datetime = Field(..., description="Message creation timestamp")
    edited_at: Optional[datetime] = Field(None, description="Message edit timestamp")
    deleted: bool = Field(..., description="Deleted status")


# ---------------------------------------------------------------------------
# History and Statistics
# ---------------------------------------------------------------------------

class ChatHistoryResponse(BaseModel):
    """Response schema for a paginated list of chat messages"""
    messages: List[ChatMessageResponse] = Field(..., description="List of messages")
    total: int = Field(..., description="Total count of messages")
    limit: int = Field(..., description="Pagination limit")
    skip: int = Field(..., description="Pagination skip")


class ChatStatisticsResponse(BaseModel):
    """Response schema for telemetry statistics"""
    sessions_created: int = Field(..., description="Total sessions created")
    sessions_archived: int = Field(..., description="Total sessions archived")
    sessions_deleted: int = Field(..., description="Total sessions deleted (soft delete)")
    messages_created: int = Field(..., description="Total messages created")
    messages_edited: int = Field(..., description="Total messages edited")
    messages_deleted: int = Field(..., description="Total messages deleted")
    average_messages_per_session: float = Field(..., description="Average messages per session")
    ai_requests: int = Field(default=0, description="Total AI requests count")
    failures: int = Field(default=0, description="Total failed requests count")
    agent_distribution: Dict[str, int] = Field(default_factory=dict, description="Counts of execution by agent name")
    average_latency: float = Field(default=0.0, description="Average response generation latency in milliseconds")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Total tokens usage details")



# Backwards compatibility aliases
ChatSessionCreateSchema = ChatSessionCreate
ChatSessionUpdateSchema = ChatSessionUpdate
ChatMessageCreateSchema = ChatMessageCreate
ChatMessageUpdateSchema = ChatMessageUpdate


# ---------------------------------------------------------------------------
# Sprint 2 AI Chat Execution Schemas
# ---------------------------------------------------------------------------

class ChatExecutionRequest(BaseModel):
    """Request schema for executing an AI message response"""
    session_id: str = Field(..., description="Reference to the chat session ID")
    message: str = Field(..., min_length=1, description="User input message text")


class ChatExecutionResponse(BaseModel):
    """Response schema returned after executing an AI query through the orchestrator"""
    assistant_message: str = Field(..., description="Final generated response from the assistant")
    agent_used: Optional[str] = Field(None, description="Winning agent name that executed the query")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="List of references or citations")
    usage: Dict[str, int] = Field(default_factory=dict, description="LLM token usage statistics")
    latency_ms: float = Field(..., description="Total execution latency in milliseconds")
    cost: float = Field(..., description="Estimated cost of workflow completion")


class ChatSessionStatisticsResponse(BaseModel):
    """Response schema summarizing session statistics and cost metrics"""
    message_count: int = Field(..., description="Total count of messages in this session")
    total_tokens: int = Field(..., description="Cumulative token count consumed by this session")
    total_cost: float = Field(..., description="Cumulative USD cost incurred by this session")
    average_latency: float = Field(..., description="Average response latency in milliseconds")
    last_agent_used: Optional[str] = Field(None, description="Last AI agent triggered for this session")

