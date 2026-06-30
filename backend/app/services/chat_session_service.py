"""
Nura - Chat Session Service
Business logic and validation for chat sessions
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionInDB,
    SessionStatus,
    SessionType,
)
from app.models.user import UserRole
from app.schemas.chat import (
    ChatSessionCreate as ChatSessionCreateSchema,
    ChatSessionUpdate as ChatSessionUpdateSchema,
    ChatSessionResponse,
)
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _session_to_response(session: ChatSessionInDB) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=session.id,
        patient_id=session.patient_id,
        title=session.title,
        description=session.description,
        status=session.status,
        session_type=session.session_type,
        active=session.active,
        last_message_at=session.last_message_at,
        message_count=session.message_count,
        total_tokens=session.total_tokens,
        total_cost=session.total_cost,
        last_agent_used=session.last_agent_used,
        pinned=session.pinned,
        archived=session.archived,
        metadata=session.metadata,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


class ChatSessionService(BaseService[ChatSessionInDB, ChatSessionCreate, ChatSessionUpdate]):
    """Service layer for chat session operations"""

    def __init__(
        self,
        chat_session_repository: ChatSessionRepository,
        user_repository: UserRepository,
    ):
        super().__init__()
        self.chat_session_repository = chat_session_repository
        self.user_repository = user_repository

    async def create_session(
        self,
        schema: ChatSessionCreateSchema,
    ) -> ChatSessionInDB:
        """Create a new chat session after validating patient user existence and role"""
        # Validate patient exists and has PATIENT role
        patient = await self.user_repository.get(schema.patient_id)
        if not patient:
            raise ValueError(f"Patient user with ID {schema.patient_id} does not exist")
        if patient.role != UserRole.PATIENT:
            raise ValueError(f"User with ID {schema.patient_id} is not a patient")

        now = utc_now()
        session_create = ChatSessionCreate(
            patient_id=schema.patient_id,
            title=schema.title,
            description=schema.description,
            session_type=schema.session_type or SessionType.AI_CHAT,
            status=SessionStatus.ACTIVE,
            active=True,
            last_message_at=now,
            message_count=0,
            total_tokens=0,
            total_cost=0.0,
            last_agent_used=None,
            pinned=False,
            archived=False,
            metadata={},
        )

        doc_dict = session_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.chat_session_repository.collection.insert_one(doc_dict)
        created = await self.chat_session_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Chat session was inserted but could not be retrieved")
        return ChatSessionInDB.from_mongo(created)

    async def get_session_by_id(self, session_id: str) -> Optional[ChatSessionInDB]:
        """Fetch a chat session by its ID"""
        session = await self.chat_session_repository.get(session_id)
        if not session or session.status == SessionStatus.DELETED:
            return None
        return session

    async def list_sessions(self, limit: int = 100, skip: int = 0) -> List[ChatSessionInDB]:
        """List all chat sessions (excluding deleted ones)"""
        return await self.chat_session_repository.list(limit=limit, skip=skip)

    async def list_sessions_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
        include_archived: bool = True
    ) -> List[ChatSessionInDB]:
        """Fetch non-deleted chat sessions for a patient"""
        return await self.chat_session_repository.get_by_patient_id(
            patient_id, limit=limit, skip=skip, include_archived=include_archived
        )

    async def list_active_sessions(
        self,
        patient_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[ChatSessionInDB]:
        """Fetch active chat sessions, optionally filtered by patient ID"""
        return await self.chat_session_repository.get_active_sessions(patient_id, limit=limit, skip=skip)

    async def rename_session(self, session_id: str, title: str) -> Optional[ChatSessionInDB]:
        """Rename a chat session"""
        update = ChatSessionUpdate(title=title)
        return await self.chat_session_repository.update(session_id, update)

    async def pin_session(self, session_id: str, pinned: bool) -> Optional[ChatSessionInDB]:
        """Pin/unpin a chat session"""
        update = ChatSessionUpdate(pinned=pinned)
        return await self.chat_session_repository.update(session_id, update)

    async def archive_session(self, session_id: str, archived: bool) -> Optional[ChatSessionInDB]:
        """Archive/unarchive a chat session"""
        status = SessionStatus.ARCHIVED if archived else SessionStatus.ACTIVE
        update = ChatSessionUpdate(archived=archived, status=status, active=not archived)
        return await self.chat_session_repository.update(session_id, update)

    async def delete_session(self, session_id: str) -> bool:
        """Soft delete a chat session record (sets status to DELETED)"""
        update = ChatSessionUpdate(status=SessionStatus.DELETED, active=False)
        result = await self.chat_session_repository.update(session_id, update)
        return result is not None

    async def restore_session(self, session_id: str) -> Optional[ChatSessionInDB]:
        """Restore a soft-deleted session back to ACTIVE"""
        update = ChatSessionUpdate(status=SessionStatus.ACTIVE, active=True)
        return await self.chat_session_repository.update(session_id, update)

    async def update_session(
        self,
        session_id: str,
        schema: ChatSessionUpdateSchema,
    ) -> Optional[ChatSessionInDB]:
        """Update an existing chat session using generic schema update"""
        update = ChatSessionUpdate(**schema.model_dump(exclude_unset=True))
        return await self.chat_session_repository.update(session_id, update)

    def to_response(self, session: ChatSessionInDB) -> ChatSessionResponse:
        """Convert internal model to API response"""
        return _session_to_response(session)
