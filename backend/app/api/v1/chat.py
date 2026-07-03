"""
Nura - Chat and Messaging Router
API endpoints for managing chat sessions, messages, and telemetry
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse

from app.models.user import UserInDB, UserRole
from app.schemas.auth import SuccessResponse
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatHistoryResponse,
    ChatStatisticsResponse,
    ChatExecutionRequest,
    ChatExecutionResponse,
    ChatSessionStatisticsResponse,
    ChatStreamChunk,
    RegenerateRequest,
    RegenerateResponse,
    FeedbackRequest,
    FeedbackResponse,
    CitationResponse,
    SuggestedQuestionsResponse,
    ConversationEvaluationResponse,
    MemoryUpdateRequest,
    MemoryUpdateResponse,
    ConversationSummaryResponse,
    MemoryStatisticsResponse,
    SessionMemoryListResponse,
    ConversationSearchResponse,
    BookmarkRequest,
    BookmarkResponse,
    ConversationMetadataResponse,
)
from app.models.chat import MessageRole
from app.core.dependencies import (
    get_current_user,
    require_exact_patient,
    require_role,
    get_chat_session_service,
    get_chat_message_service,
    get_chat_execution_service,
    get_chat_message_repository,
    get_chat_streaming_service,
    get_regeneration_service,
    get_feedback_service,
    get_citation_service,
    get_conversation_intelligence_service,
    get_conversation_evaluator,
    get_memory_update_service,
    get_vector_service,
    get_conversation_search_service,
    get_export_service,
    get_bookmark_service,
)
from app.repositories.chat_message_repository import ChatMessageRepository
from app.services.chat_session_service import ChatSessionService
from app.services.chat_message_service import ChatMessageService
from app.services.chat.chat_execution_service import ChatExecutionService
from app.services.chat.chat_streaming_service import ChatStreamingService
from app.services.chat.regeneration_service import RegenerationService
from app.services.chat_memory.conversation_evaluator import ConversationEvaluator
from app.services.chat_memory.memory_update_service import MemoryUpdateService
from app.services.vector_service import VectorService
from app.services.chat.feedback_service import FeedbackService
from app.services.chat.citation_service import CitationService
from app.services.chat.conversation_intelligence import ConversationIntelligenceService
from app.services.chat.conversation_search_service import ConversationSearchService
from app.services.chat.export_service import ExportService
from app.services.chat.bookmark_service import BookmarkService
from app.services.chat.telemetry import get_chat_statistics
from app.db import get_database

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Sessions Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/session",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Chat Session",
    description="Creates a new chat session for a patient."
)
async def create_session(
    schema: ChatSessionCreate,
    current_user: UserInDB = Depends(require_exact_patient),
    service: ChatSessionService = Depends(get_chat_session_service),
) -> SuccessResponse:
    # Ensure patient_id in schema matches the logged-in user
    if schema.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create chat sessions for other patients"
        )
    try:
        session = await service.create_session(schema)
        return SuccessResponse(
            success=True,
            message="Chat session created successfully",
            data=service.to_response(session).model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Failed to create chat session")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create chat session")


@router.get(
    "/sessions",
    response_model=SuccessResponse,
    summary="List Chat Sessions",
    description="Retrieves chat sessions for the logged-in patient, sorted by pinned first, then newest first."
)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    include_archived: bool = Query(True),
    current_user: UserInDB = Depends(require_exact_patient),
    service: ChatSessionService = Depends(get_chat_session_service),
) -> SuccessResponse:
    try:
        sessions = await service.list_sessions_by_patient(
            patient_id=current_user.id,
            limit=limit,
            skip=skip,
            include_archived=include_archived
        )
        return SuccessResponse(
            success=True,
            message="Chat sessions retrieved successfully",
            data={
                "sessions": [service.to_response(s).model_dump() for s in sessions],
                "limit": limit,
                "skip": skip
            }
        )
    except Exception as e:
        logger.exception("Failed to list chat sessions")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list chat sessions")


@router.get(
    "/session/{session_id}",
    response_model=SuccessResponse,
    summary="Get Chat Session Details",
    description="Retrieves a single chat session by ID."
)
async def get_session(
    session_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    service: ChatSessionService = Depends(get_chat_session_service),
) -> SuccessResponse:
    session = await service.get_session_by_id(session_id)
    if not session or session.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    return SuccessResponse(
        success=True,
        message="Chat session details retrieved successfully",
        data=service.to_response(session).model_dump()
    )


@router.patch(
    "/session/{session_id}",
    response_model=SuccessResponse,
    summary="Update Chat Session",
    description="Updates chat session details like title, pinned, or archived state."
)
async def update_session(
    session_id: str,
    schema: ChatSessionUpdate,
    current_user: UserInDB = Depends(require_exact_patient),
    service: ChatSessionService = Depends(get_chat_session_service),
) -> SuccessResponse:
    session = await service.get_session_by_id(session_id)
    if not session or session.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    try:
        updated = await service.update_session(session_id, schema)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update chat session"
            )
        return SuccessResponse(
            success=True,
            message="Chat session updated successfully",
            data=service.to_response(updated).model_dump()
        )
    except Exception as e:
        logger.exception("Failed to update chat session")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update chat session")


@router.delete(
    "/session/{session_id}",
    response_model=SuccessResponse,
    summary="Delete Chat Session",
    description="Soft-deletes a chat session."
)
async def delete_session(
    session_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    service: ChatSessionService = Depends(get_chat_session_service),
) -> SuccessResponse:
    session = await service.get_session_by_id(session_id)
    if not session or session.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    try:
        success = await service.delete_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete chat session"
            )
        return SuccessResponse(
            success=True,
            message="Chat session deleted successfully"
        )
    except Exception as e:
        logger.exception("Failed to delete chat session")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete chat session")


# ---------------------------------------------------------------------------
# Messages Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/message",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store Chat Message",
    description="Persists a chat message in the database (no AI execution is run)."
)
async def create_message(
    schema: ChatMessageCreate,
    current_user: UserInDB = Depends(require_exact_patient),
    service: ChatMessageService = Depends(get_chat_message_service),
) -> SuccessResponse:
    # Ensure patient_id in schema matches the logged-in user
    if schema.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot store chat messages for other patients"
        )
    try:
        message = await service.create_message(schema)
        return SuccessResponse(
            success=True,
            message="Message stored successfully",
            data=service.to_response(message).model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Failed to store message")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to store message")


@router.get(
    "/messages/{session_id}",
    response_model=SuccessResponse,
    summary="Get Chat History",
    description="Retrieves a paginated list of chat history for a session."
)
async def get_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: UserInDB = Depends(require_exact_patient),
    session_service: ChatSessionService = Depends(get_chat_session_service),
    message_service: ChatMessageService = Depends(get_chat_message_service),
) -> SuccessResponse:
    session = await session_service.get_session_by_id(session_id)
    if not session or session.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    try:
        messages = await message_service.list_messages_by_session(
            session_id=session_id,
            limit=limit,
            skip=skip
        )
        
        # Calculate total messages (excluding deleted)
        total = await message_service.chat_message_repository.count({
            "session_id": session_id,
            "deleted": {"$ne": True}
        })
        
        history_response = ChatHistoryResponse(
            messages=[message_service.to_response(msg) for msg in messages],
            total=total,
            limit=limit,
            skip=skip
        )
        return SuccessResponse(
            success=True,
            message="Conversation history retrieved successfully",
            data=history_response.model_dump()
        )
    except Exception as e:
        logger.exception("Failed to get messages history")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve history")


@router.post(
    "/message/execute",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Message through AI Orchestrator",
    description="Stores the user message, invokes the Multi-Agent Orchestrator, and returns the response."
)
async def execute_message(
    schema: ChatExecutionRequest,
    current_user: UserInDB = Depends(require_exact_patient),
    execution_service: ChatExecutionService = Depends(get_chat_execution_service),
) -> SuccessResponse:
    try:
        response = await execution_service.execute_chat_message(
            session_id=schema.session_id,
            patient_id=current_user.id,
            message=schema.message
        )
        return SuccessResponse(
            success=True,
            message="AI execution complete",
            data=response.model_dump()
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("AI Chat execution crashed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/session/{session_id}/statistics",
    response_model=SuccessResponse,
    summary="Get Chat Session Statistics",
    description="Retrieves message count, total tokens, cost, latency, and last agent for a single session."
)
async def get_session_statistics(
    session_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    session_service: ChatSessionService = Depends(get_chat_session_service),
    message_repo: ChatMessageRepository = Depends(get_chat_message_repository),
) -> SuccessResponse:
    session = await session_service.get_session_by_id(session_id)
    if not session or session.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    try:
        # Fetch all messages in the session
        messages = await message_repo.get_by_session_id(
            session_id=session_id,
            limit=1000,
            skip=0,
            include_deleted=False
        )

        message_count = len(messages)
        
        # Calculate tokens sum
        total_tokens = 0
        assistant_latencies = []
        
        for msg in messages:
            if msg.role == MessageRole.ASSISTANT:
                usage = msg.token_usage or {}
                total_tokens += usage.get("total_tokens", 0)
                if msg.latency_ms is not None:
                    assistant_latencies.append(msg.latency_ms)

        average_latency = 0.0
        if assistant_latencies:
            average_latency = sum(assistant_latencies) / len(assistant_latencies)

        stats = ChatSessionStatisticsResponse(
            message_count=message_count,
            total_tokens=total_tokens,
            total_cost=session.total_cost,
            average_latency=average_latency,
            last_agent_used=session.last_agent_used,
        )

        return SuccessResponse(
            success=True,
            message="Session statistics retrieved successfully",
            data=stats.model_dump()
        )
    except Exception as e:
        logger.exception("Failed to retrieve chat session statistics")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve session statistics")


@router.post(
    "/message/stream",
    summary="Stream Message response via SSE",
    description="Invokes the orchestrator and streams chunks via Server-Sent Events (SSE)."
)
async def stream_message(
    schema: ChatExecutionRequest,
    current_user: UserInDB = Depends(require_exact_patient),
    streaming_service: ChatStreamingService = Depends(get_chat_streaming_service),
) -> StreamingResponse:
    generator = streaming_service.stream_chat_message(
        session_id=schema.session_id,
        patient_id=current_user.id,
        message=schema.message
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.post(
    "/message/regenerate",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Regenerate Last Response",
    description="Regenerates the latest assistant message response in the session."
)
async def regenerate_message(
    schema: RegenerateRequest,
    current_user: UserInDB = Depends(require_exact_patient),
    regen_service: RegenerationService = Depends(get_regeneration_service),
) -> SuccessResponse:
    try:
        response = await regen_service.regenerate_latest_response(
            session_id=schema.session_id,
            patient_id=current_user.id
        )
        return SuccessResponse(
            success=True,
            message="Response regenerated successfully",
            data=response.model_dump()
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("AI Response regeneration crashed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/message/feedback",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit User Feedback",
    description="Submits helpful / unhelpful rating feedback for a message."
)
async def submit_feedback(
    schema: FeedbackRequest,
    current_user: UserInDB = Depends(require_exact_patient),
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> SuccessResponse:
    try:
        success = await feedback_service.submit_feedback(
            message_id=schema.message_id,
            patient_id=current_user.id,
            rating=schema.rating,
            comment=schema.comment
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to save feedback")
        return SuccessResponse(
            success=True,
            message="Feedback saved successfully"
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Failed to submit message feedback")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/message/{message_id}/citations",
    response_model=SuccessResponse,
    summary="Get Message Citations",
    description="Retrieves clean UI-friendly citation metadata matches for an assistant response."
)
async def get_message_citations(
    message_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    citation_service: CitationService = Depends(get_citation_service),
) -> SuccessResponse:
    try:
        citations = await citation_service.get_message_citations(
            message_id=message_id,
            patient_id=current_user.id
        )
        return SuccessResponse(
            success=True,
            message="Citations retrieved successfully",
            data=[c.model_dump() for c in citations]
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception("Failed to fetch message citations")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/message/{message_id}/followups",
    response_model=SuccessResponse,
    summary="Get Message Followup Questions",
    description="Generates automatic suggested follow-up questions and auto-names untitled conversations."
)
async def get_followup_questions(
    message_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    message_repo: ChatMessageRepository = Depends(get_chat_message_repository),
    intelligence_service: ConversationIntelligenceService = Depends(get_conversation_intelligence_service),
) -> SuccessResponse:
    msg = await message_repo.get(message_id)
    if not msg or msg.patient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    
    # Fetch the previous user query if possible to build context
    user_query = "review medical file"
    try:
        session_msgs = await message_repo.get_by_session_id(msg.session_id, limit=20, skip=0, include_deleted=False)
        for idx, m in enumerate(session_msgs):
            if m.id == msg.id and idx > 0:
                user_query = session_msgs[idx - 1].content
                break
    except Exception:
        pass

    try:
        intel = await intelligence_service.generate_intelligence(user_query, msg.content)
        # Automatically rename the session if currently untitled
        await intelligence_service.update_session_title_if_untitled(msg.session_id, intel["title"])
        
        return SuccessResponse(
            success=True,
            message="Follow-up questions retrieved successfully",
            data={"questions": intel["suggested_questions"]}
        )
    except Exception as e:
        logger.exception("Failed to compile follow-up questions")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/memory/evaluate",
    response_model=SuccessResponse,
    summary="Evaluate Conversation Memory",
    description="Evaluates worthiness of conversation session for memory storage without saving it. Admin only."
)
async def evaluate_conversation_memory(
    schema: MemoryUpdateRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    evaluator: ConversationEvaluator = Depends(get_conversation_evaluator),
) -> SuccessResponse:
    try:
        results = await evaluator.evaluate_session(schema.session_id)
        validated = ConversationEvaluationResponse(**results)
        return SuccessResponse(
            success=True,
            message="Evaluation complete",
            data=validated.model_dump()
        )
    except Exception as e:
        logger.exception("Failed to evaluate conversation worthiness")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/memory/update",
    response_model=SuccessResponse,
    summary="Force Memory Synchronization",
    description="Forces evaluation and updates structured patient memory and semantic chat memory collections. Admin only."
)
async def force_memory_update(
    schema: MemoryUpdateRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    update_service: MemoryUpdateService = Depends(get_memory_update_service),
    message_repo: ChatMessageRepository = Depends(get_chat_message_repository),
    session_service: ChatSessionService = Depends(get_chat_session_service),
) -> SuccessResponse:
    try:
        messages = await message_repo.get_by_session_id(schema.session_id, limit=200, skip=0, include_deleted=False)
        message_ids = [m.id for m in messages]
        
        session = await session_service.get_session_by_id(schema.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        results = await update_service.evaluate_and_sync_session(
            session_id=schema.session_id,
            patient_id=session.patient_id,
            message_ids=message_ids
        )
        
        status_str = results.get("status", "skipped")
        res = MemoryUpdateResponse(
            success=True,
            status=f"Session synchronization complete: {status_str}"
        )
        return SuccessResponse(
            success=True,
            message="Memory update synchronized",
            data=res.model_dump()
        )
    except Exception as e:
        logger.exception("Failed to force synchronize session memory")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/memory/statistics",
    response_model=SuccessResponse,
    summary="Get Memory Telemetry",
    description="Returns global memory sync metrics, evaluation distributions, and latencies. Admin only."
)
async def get_memory_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
) -> SuccessResponse:
    try:
        from app.services.chat_memory.telemetry import memory_telemetry
        stats = memory_telemetry.get_statistics()
        validated = MemoryStatisticsResponse(**stats)
        return SuccessResponse(
            success=True,
            message="Memory statistics retrieved successfully",
            data=validated.model_dump()
        )
    except Exception as e:
        logger.exception("Failed to retrieve memory statistics")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/session/{session_id}/memory",
    response_model=SessionMemoryListResponse,
    summary="Get Session Memory",
    description="Retrieves computed semantic RAG summaries and keywords saved in Qdrant for this session."
)
async def get_session_memory(
    session_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    session_service: ChatSessionService = Depends(get_chat_session_service),
    vector_service: VectorService = Depends(get_vector_service),
) -> SuccessResponse:
    try:
        session = await session_service.get_session_by_id(session_id)
        if not session or session.patient_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        # Scroll chat_memory from Qdrant matching session_id
        await vector_service.create_collection("chat_memory")
        points, _ = await vector_service.scroll(
            collection_name="chat_memory",
            filter_dict={"session_id": session_id},
            limit=50
        )
        
        memories = []
        for p in points:
            payload = p.get("payload", {})
            memories.append({
                "summary": payload.get("summary", ""),
                "keywords": payload.get("keywords", []),
                "entities": payload.get("entities", []),
                "timestamp": payload.get("timestamp", "")
            })
            
        return SessionMemoryListResponse(
            success=True,
            message="Session memory details retrieved",
            data=memories
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Failed to fetch session memories from Qdrant")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ---------------------------------------------------------------------------
# Admin Telemetry Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/statistics",
    response_model=SuccessResponse,
    summary="Get Chat Statistics",
    description="Admin-only endpoint retrieving real-time chat telemetry."
)
async def get_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
) -> SuccessResponse:
    try:
        db = get_database()
        stats = await get_chat_statistics(db)
        # Validate structure with Pydantic schema
        validated_stats = ChatStatisticsResponse(**stats)
        return SuccessResponse(
            success=True,
            message="Chat statistics retrieved successfully",
            data=validated_stats.model_dump()
        )
    except Exception as e:
        logger.exception("Failed to retrieve chat statistics")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve statistics")


# ---------------------------------------------------------------------------
# Search, Export, and Bookmarks Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/search",
    response_model=SuccessResponse,
    summary="Search Conversations",
    description="Returns conversations and messages matching a full-text query with highlights."
)
async def search_conversations(
    query: str = Query(..., description="Query term to search"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    favorites: Optional[bool] = Query(None, description="Filter by favorite pinned sessions"),
    archived: Optional[bool] = Query(None, description="Filter by archived sessions"),
    agent: Optional[str] = Query(None, description="Filter by AI agent used"),
    current_user: UserInDB = Depends(require_exact_patient),
    search_service: ConversationSearchService = Depends(get_conversation_search_service)
) -> SuccessResponse:
    try:
        results = await search_service.search_conversations(
            patient_id=current_user.id,
            query=query,
            session_id=session_id,
            date_from=date_from,
            date_to=date_to,
            favorites=favorites,
            archived=archived,
            agent=agent
        )
        return SuccessResponse(
            success=True,
            message="Search results compiled",
            data=results.model_dump()
        )
    except Exception as e:
        logger.exception("Failed to search conversations")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/export/{session_id}",
    summary="Export Conversation History",
    description="Downloads conversation transcript in Markdown, PDF, or JSON format."
)
async def export_conversation(
    session_id: str,
    format: str = Query("md", regex="^(md|pdf|json)$", description="File format: md, pdf, or json"),
    current_user: UserInDB = Depends(require_exact_patient),
    export_service: ExportService = Depends(get_export_service)
):
    try:
        data = await export_service.get_export_data(session_id, current_user.id)
        session = data["session"]
        messages = data["messages"]

        if format == "json":
            content = export_service.export_as_json(session, messages)
            media_type = "application/json"
            filename = f"conversation_{session_id}.json"
        elif format == "pdf":
            content = export_service.export_as_pdf(session, messages)
            media_type = "application/pdf"
            filename = f"conversation_{session_id}.pdf"
        else:
            content = export_service.export_as_markdown(session, messages)
            media_type = "text/markdown"
            filename = f"conversation_{session_id}.md"

        headers = {
            "Content-Disposition": f"attachment; filename={filename}"
        }
        return Response(content=content, media_type=media_type, headers=headers)
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        logger.exception("Failed to export conversation")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/bookmark",
    response_model=SuccessResponse,
    summary="Bookmark Chat Message",
    description="Bookmarks a specific assistant or user message log."
)
async def add_bookmark(
    schema: BookmarkRequest,
    current_user: UserInDB = Depends(require_exact_patient),
    bookmark_service: BookmarkService = Depends(get_bookmark_service)
) -> SuccessResponse:
    try:
        res = await bookmark_service.add_bookmark(current_user.id, schema.message_id)
        return SuccessResponse(
            success=True,
            message="Message bookmarked successfully",
            data=res.model_dump()
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        logger.exception("Failed to add message bookmark")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/bookmark/{message_id}",
    response_model=SuccessResponse,
    summary="Delete Chat Bookmark",
    description="Removes bookmark metadata from a message."
)
async def remove_bookmark(
    message_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    bookmark_service: BookmarkService = Depends(get_bookmark_service)
) -> SuccessResponse:
    try:
        removed = await bookmark_service.remove_bookmark(current_user.id, message_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        return SuccessResponse(
            success=True,
            message="Bookmark removed successfully",
            data={"deleted": True}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Failed to remove bookmark")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/bookmarks",
    response_model=SuccessResponse,
    summary="List Bookmarked Messages",
    description="Retrieves scroll history list of patient's bookmarked message logs."
)
async def list_bookmarks(
    current_user: UserInDB = Depends(require_exact_patient),
    bookmark_service: BookmarkService = Depends(get_bookmark_service)
) -> SuccessResponse:
    try:
        bookmarks = await bookmark_service.get_bookmarks(current_user.id)
        return SuccessResponse(
            success=True,
            message="Bookmarked messages retrieved",
            data={"bookmarks": [b.model_dump() for b in bookmarks]}
        )
    except Exception as e:
        logger.exception("Failed to list bookmarked messages")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Sprint 7: Operational & Telemetry Dashboards (Admin Only)
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=SuccessResponse,
    summary="Get Subsystem Health",
    description="Returns connection health and configurations (Admin only)."
)
async def get_health(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> SuccessResponse:
    try:
        from app.services.chat.health_monitor import get_health_monitor
        monitor = get_health_monitor()
        health = await monitor.check_health()
        return SuccessResponse(
            success=True,
            message="Subsystems health checked",
            data=health
        )
    except Exception as e:
        logger.exception("Failed to check subsystems health")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/statistics",
    response_model=SuccessResponse,
    summary="Get Analytics & Metrics",
    description="Returns aggregate chat operational intelligence reports (Admin only)."
)
async def get_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> SuccessResponse:
    try:
        from app.services.chat.analytics_service import get_analytics_service
        service = get_analytics_service()
        stats = await service.get_analytics()
        return SuccessResponse(
            success=True,
            message="Operational analytics retrieved",
            data=stats
        )
    except Exception as e:
        logger.exception("Failed to retrieve statistics")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/cache",
    response_model=SuccessResponse,
    summary="Get Cache Operational Stats",
    description="Returns size, hits, misses, and hit ratio of internal TTL caches (Admin only)."
)
async def get_cache_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> SuccessResponse:
    try:
        from app.services.chat.cache_service import get_chat_cache_service
        cache_svc = get_chat_cache_service()
        stats = cache_svc.get_statistics()
        return SuccessResponse(
            success=True,
            message="Cache statistics retrieved",
            data=stats
        )
    except Exception as e:
        logger.exception("Failed to retrieve cache statistics")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/performance",
    response_model=SuccessResponse,
    summary="Get Latency & Performance Performance",
    description="Returns average request execution, streaming, and RAG latencies (Admin only)."
)
async def get_performance_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> SuccessResponse:
    try:
        from app.services.chat.telemetry_service import get_extended_telemetry
        stats = get_extended_telemetry().get_stats()
        return SuccessResponse(
            success=True,
            message="Performance metrics retrieved",
            data=stats.get("performance", {})
        )
    except Exception as e:
        logger.exception("Failed to retrieve performance metrics")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/streaming/statistics",
    response_model=SuccessResponse,
    summary="Get Streaming Lifecycle Analytics",
    description="Returns started, completed, cancelled, and failed streams counts (Admin only)."
)
async def get_streaming_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> SuccessResponse:
    try:
        from app.services.chat.telemetry_service import get_extended_telemetry
        stats = get_extended_telemetry().get_stats()
        return SuccessResponse(
            success=True,
            message="Streaming metrics retrieved",
            data=stats.get("streaming", {})
        )
    except Exception as e:
        logger.exception("Failed to retrieve streaming metrics")
        raise HTTPException(status_code=500, detail=str(e))
