"""
Nura - Chat and Messaging Router
API endpoints for managing chat sessions, messages, and telemetry
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

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
)
from app.core.dependencies import (
    get_current_user,
    require_exact_patient,
    require_role,
    get_chat_session_service,
    get_chat_message_service,
)
from app.services.chat_session_service import ChatSessionService
from app.services.chat_message_service import ChatMessageService
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
