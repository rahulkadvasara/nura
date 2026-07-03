"""
Nura - Chat Message Service
Business logic and validation for chat messages
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.chat import (
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageInDB,
    MessageRole,
    ChatSessionUpdate,
)
from app.models.user import UserRole
from app.schemas.chat import (
    ChatMessageCreate as ChatMessageCreateSchema,
    ChatMessageUpdate as ChatMessageUpdateSchema,
    ChatMessageResponse,
)
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _message_to_response(message: ChatMessageInDB) -> ChatMessageResponse:
    cards = None
    actions = None
    if message.metadata:
        if "cards" in message.metadata:
            cards = message.metadata["cards"]
        if "actions" in message.metadata:
            actions = message.metadata["actions"]

    return ChatMessageResponse(
        id=message.id,
        session_id=message.session_id,
        patient_id=message.patient_id,
        role=message.role,
        content=message.content,
        citations=message.citations,
        attachments=message.attachments,
        token_usage=message.token_usage,
        latency_ms=message.latency_ms,
        metadata=message.metadata,
        created_at=message.created_at,
        edited_at=message.edited_at,
        deleted=message.deleted,
        cards=cards,
        actions=actions,
    )


class ChatMessageService(BaseService[ChatMessageInDB, ChatMessageCreate, ChatMessageUpdate]):
    """Service layer for chat message operations"""

    def __init__(
        self,
        chat_message_repository: ChatMessageRepository,
        chat_session_repository: ChatSessionRepository,
        user_repository: UserRepository,
    ):
        super().__init__()
        self.chat_message_repository = chat_message_repository
        self.chat_session_repository = chat_session_repository
        self.user_repository = user_repository

    async def create_message(
        self,
        schema: ChatMessageCreateSchema,
    ) -> ChatMessageInDB:
        """Create a new chat message record and update session stats"""
        # Validate session exists
        session = await self.chat_session_repository.get(schema.session_id)
        if not session:
            raise ValueError(f"Chat session with ID {schema.session_id} does not exist")

        # Validate patient exists
        patient = await self.user_repository.get(schema.patient_id)
        if not patient:
            raise ValueError(f"Patient user with ID {schema.patient_id} does not exist")

        now = utc_now()
        message_create = ChatMessageCreate(
            session_id=schema.session_id,
            patient_id=schema.patient_id,
            role=schema.role,
            content=schema.content,
            citations=schema.citations or [],
            attachments=schema.attachments or [],
            token_usage=schema.token_usage or {},
            latency_ms=schema.latency_ms,
            metadata=schema.metadata or {},
            deleted=False,
        )

        doc_dict = message_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["edited_at"] = None

        result = await self.chat_message_repository.collection.insert_one(doc_dict)
        created = await self.chat_message_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Chat message was inserted but could not be retrieved")

        # Update the chat session stats (message count, last message timestamp, tokens)
        msg_tokens = sum((schema.token_usage or {}).values()) if schema.token_usage else 0
        new_total_tokens = session.total_tokens + msg_tokens
        
        session_update = ChatSessionUpdate(
            last_message_at=now,
            message_count=session.message_count + 1,
            total_tokens=new_total_tokens,
        )
        # If assistant message has an agent in metadata, update it
        if schema.role == MessageRole.ASSISTANT and schema.metadata:
            agent = schema.metadata.get("agent") or schema.metadata.get("last_agent_used")
            if agent:
                session_update.last_agent_used = str(agent)

        await self.chat_session_repository.update(schema.session_id, session_update)

        return ChatMessageInDB.from_mongo(created)

    async def get_message_by_id(self, message_id: str) -> Optional[ChatMessageInDB]:
        """Fetch a chat message by its ID"""
        return await self.chat_message_repository.get(message_id)

    async def list_messages_by_session(
        self,
        session_id: str,
        limit: int = 100,
        skip: int = 0,
        include_deleted: bool = False,
    ) -> List[ChatMessageInDB]:
        """Fetch all non-deleted messages for a given session ID, sorted chronologically"""
        return await self.chat_message_repository.get_by_session_id(
            session_id, limit=limit, skip=skip, include_deleted=include_deleted
        )

    async def update_message(
        self,
        message_id: str,
        schema: ChatMessageUpdateSchema,
    ) -> Optional[ChatMessageInDB]:
        """Update an existing chat message"""
        update = ChatMessageUpdate(**schema.model_dump(exclude_unset=True))
        update.edited_at = utc_now()
        return await self.chat_message_repository.update(message_id, update)

    async def delete_message(self, message_id: str) -> bool:
        """Soft delete a chat message (sets deleted flag to True)"""
        update = ChatMessageUpdate(deleted=True)
        result = await self.chat_message_repository.update(message_id, update)
        return result is not None

    def to_response(self, message: ChatMessageInDB) -> ChatMessageResponse:
        """Convert internal model to API response"""
        return _message_to_response(message)
