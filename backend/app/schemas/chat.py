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
# Sprint 6 Chat Dashboard & Healthcare Cards Schemas
# ---------------------------------------------------------------------------

class RichCardAction(BaseModel):
    """Structured action/CTA buttons on cards"""
    action_type: str = Field(..., description="Action ID: OPEN_REPORT, DOWNLOAD_REPORT, VIEW_DOCTOR, BOOK_APPOINTMENT, CREATE_REMINDER, VIEW_REMINDER, VIEW_MEDICATION, CHECK_DRUG_SAFETY, VIEW_RISK_ANALYSIS, VIEW_LABORATORY_RESULTS")
    label: str = Field(..., description="Readable label")
    url: str = Field(..., description="Deep link URL path")
    method: str = Field("GET", description="HTTP request method")
    payload: Optional[Dict[str, Any]] = Field(None, description="Optional request payload parameters")

class RichCardResponse(BaseModel):
    """Base schema for structured healthcare dashboard cards"""
    card_type: str = Field(..., description="Card type: report, medication, drug_safety, appointment, reminder, doctor, laboratory, risk")
    title: str = Field(..., description="Descriptive card title")
    subtitle: Optional[str] = Field(None, description="Secondary card subtitle details")
    icon: Optional[str] = Field(None, description="Lucide icon name string")
    status: Optional[str] = Field(None, description="Badge status string")
    summary: Optional[str] = Field(None, description="Short textual summary content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")
    actions: List[RichCardAction] = Field(default_factory=list, description="List of card actions")

class ReportCard(RichCardResponse):
    """Structured medical report card representation"""
    pass

class MedicationCard(RichCardResponse):
    """Structured prescribed medication card representation"""
    pass

class AppointmentCard(RichCardResponse):
    """Structured consultation appointment card representation"""
    pass

class ReminderCard(RichCardResponse):
    """Structured patient reminder alert card representation"""
    pass

class DoctorCard(RichCardResponse):
    """Structured doctor profile reference card representation"""
    pass

class RiskCard(RichCardResponse):
    """Structured clinical risk findings card representation"""
    pass

class LaboratoryCard(RichCardResponse):
    """Structured parsed laboratory test card representation"""
    pass


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
    cards: Optional[List[RichCardResponse]] = Field(None, description="Healthcare cards attached")
    actions: Optional[List[RichCardAction]] = Field(None, description="Healthcare actions attached")


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
    cards: List[RichCardResponse] = Field(default_factory=list, description="Structured healthcare cards attached")
    actions: List[RichCardAction] = Field(default_factory=list, description="Interactive actions/CTAs")


class ChatSessionStatisticsResponse(BaseModel):
    """Response schema summarizing session statistics and cost metrics"""
    message_count: int = Field(..., description="Total count of messages in this session")
    total_tokens: int = Field(..., description="Cumulative token count consumed by this session")
    total_cost: float = Field(..., description="Cumulative USD cost incurred by this session")
    average_latency: float = Field(..., description="Average response latency in milliseconds")
    last_agent_used: Optional[str] = Field(None, description="Last AI agent triggered for this session")


# ---------------------------------------------------------------------------
# Sprint 3 Streaming & Intelligence Schemas
# ---------------------------------------------------------------------------

class ChatStreamChunk(BaseModel):
    """Schema representing a single Server-Sent Event (SSE) chunk payload"""
    type: str = Field(..., description="Chunk type: 'token', 'metadata', or 'error'")
    content: Optional[str] = Field(None, description="Partial text content chunk")
    agent_used: Optional[str] = Field(None, description="AI agent executed")
    citations: Optional[List[Dict[str, Any]]] = Field(None, description="Citations list if type=metadata")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage details")
    latency_ms: Optional[float] = Field(None, description="Latency details")
    cost: Optional[float] = Field(None, description="Cost details")
    error: Optional[str] = Field(None, description="Error message details if type=error")
    cards: Optional[List[RichCardResponse]] = Field(None, description="Healthcare cards list if type=metadata")
    actions: Optional[List[RichCardAction]] = Field(None, description="Interactive actions list if type=metadata")


class RegenerateRequest(BaseModel):
    """Request schema to regenerate the latest assistant response in a session"""
    session_id: str = Field(..., description="Reference to the chat session ID")


class RegenerateResponse(BaseModel):
    """Response schema returned after regenerating assistant message response"""
    assistant_message: str = Field(..., description="Newly generated response")
    agent_used: Optional[str] = Field(None, description="Agent executed")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations")
    usage: Dict[str, int] = Field(default_factory=dict, description="Usage")
    latency_ms: float = Field(..., description="Latency")
    cost: float = Field(..., description="Estimated cost")


class FeedbackRequest(BaseModel):
    """Request schema for submitting message feedback"""
    message_id: str = Field(..., description="Reference to the chat message ID")
    rating: str = Field(..., description="Rating rating: 'helpful' or 'unhelpful'")
    comment: Optional[str] = Field(None, description="Optional text comment")


class FeedbackResponse(BaseModel):
    """Response schema for feedback acknowledgement"""
    success: bool = Field(..., description="Success check")
    message: str = Field(..., description="Status message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional feedback metadata")


class CitationResponse(BaseModel):
    """Response schema for formatted UI-friendly citations"""
    document: str = Field(..., description="Document type or clinical record ID")
    source: str = Field(..., description="File source or collection origin")
    page: Optional[int] = Field(None, description="Page number details if applicable")
    section: Optional[str] = Field(None, description="Clinical section matched")
    confidence: Optional[float] = Field(None, description="Matching confidence score (0.0 - 1.0)")
    report_title: Optional[str] = Field(None, description="Title of the source report document")
    clickable_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional click-through details/links")


class SuggestedQuestionsResponse(BaseModel):
    """Response schema listing suggested follow-up prompts"""
    questions: List[str] = Field(..., description="List of generated question prompts")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata containing tags, last topic, and category")


# ---------------------------------------------------------------------------
# Sprint 4 Memory & Intelligence Schemas
# ---------------------------------------------------------------------------

class ConversationEvaluationResponse(BaseModel):
    """Response schema summarizing conversation worthiness scores"""
    memory_score: float = Field(..., description="Overall memory worthiness score")
    semantic_score: float = Field(..., description="Semantic value score")
    clinical_score: float = Field(..., description="Clinical relevance score")
    should_store_chat_memory: bool = Field(..., description="Whether to store in Qdrant chat_memory")
    should_update_patient_memory: bool = Field(..., description="Whether to update structured MongoDB patient_memory")


class MemoryUpdateRequest(BaseModel):
    """Request schema to force memory evaluation and synchronization for a session"""
    session_id: str = Field(..., description="Session ID to synchronize memory for")


class MemoryUpdateResponse(BaseModel):
    """Response schema for memory update check status"""
    success: bool = Field(..., description="Indicates if sync finished successfully")
    status: str = Field(..., description="Summary status statement")


class ConversationSummaryResponse(BaseModel):
    """Response schema representing computed memory summary payload details"""
    summary: str = Field(..., description="Consolidated semantic RAG-optimized summary text")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    entities: List[str] = Field(default_factory=list, description="Extracted clinical entities")


class MemoryStatisticsResponse(BaseModel):
    """Response schema returning memory pipeline execution statistics"""
    evaluations_count: int = Field(..., description="Total sessions evaluated")
    stored_count: int = Field(..., description="Total evaluations resulting in database storage")
    skipped_count: int = Field(..., description="Total sessions skipped")
    patient_memory_updates: int = Field(..., description="Total MongoDB updates performed")
    qdrant_updates: int = Field(..., description="Total Qdrant points upserted")
    avg_scores: Dict[str, float] = Field(..., description="Score aggregates dictionary")


class SessionMemoryListResponse(BaseModel):
    """Success response wrapper specifically for list response payload data"""
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Success message")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Response list data")


class SearchHit(BaseModel):
    """Represents a single match within conversation search"""
    session_id: str = Field(..., description="Matching session ID")
    session_title: str = Field(..., description="Title of matching session")
    message_id: Optional[str] = Field(None, description="Optional ID of matching message")
    role: Optional[str] = Field(None, description="Optional message role")
    content: str = Field(..., description="Content snippet")
    highlighted_snippet: str = Field(..., description="Content snippet with <mark> highlighting")
    timestamp: datetime = Field(..., description="Timestamp of match")


class ConversationSearchRequest(BaseModel):
    """Request query payload for full-text search"""
    query: str = Field(..., description="Search query term")
    session_id: Optional[str] = Field(None, description="Filter by session ID")
    date_from: Optional[datetime] = Field(None, description="Filter from start date")
    date_to: Optional[datetime] = Field(None, description="Filter to end date")


class ConversationSearchResponse(BaseModel):
    """Response containing matched search results"""
    results: List[SearchHit] = Field(default_factory=list, description="List of search result hits")


class ExportResponse(BaseModel):
    """Export status metadata wrapper"""
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Success message")
    download_url: Optional[str] = Field(None, description="Optional relative URL for download stream")


class BookmarkRequest(BaseModel):
    """Request payload to bookmark a chat message"""
    message_id: str = Field(..., description="Message ID to bookmark")


class BookmarkResponse(BaseModel):
    """Response representation of a chat bookmark"""
    id: str = Field(..., description="Bookmark ID")
    message_id: str = Field(..., description="ID of bookmarked message")
    session_id: str = Field(..., description="ID of chat session")
    patient_id: str = Field(..., description="User ID of patient")
    bookmarked_at: datetime = Field(..., description="Timestamp bookmarked")
    message_content: str = Field(..., description="Cached message content")
    message_role: str = Field(..., description="Cached role string")


class ConversationMetadataResponse(BaseModel):
    """Incremental metadata details for a session"""
    session_id: str = Field(..., description="Session ID")
    title: str = Field(..., description="Descriptive session title")
    summary: str = Field(..., description="Incremental AI-generated summary")
    tags: List[str] = Field(default_factory=list, description="Clinical/topic tags")
    last_topic: str = Field(..., description="Last active topic discussed")
    category: str = Field(..., description="Clinical categorization")




