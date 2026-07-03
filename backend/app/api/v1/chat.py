"""
Nura - Chat and Messaging Router
API endpoints for managing chat sessions, messages, and telemetry
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
)
from app.repositories.chat_message_repository import ChatMessageRepository
from app.services.chat_session_service import ChatSessionService
from app.services.chat_message_service import ChatMessageService
from app.services.chat.chat_execution_service import ChatExecutionService
from app.services.chat.chat_streaming_service import ChatStreamingService
from app.services.chat.regeneration_service import RegenerationService
from app.services.chat.feedback_service import FeedbackService
from app.services.chat.citation_service import CitationService
from app.services.chat.conversation_intelligence import ConversationIntelligenceService
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
