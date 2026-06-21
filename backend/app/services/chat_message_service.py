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
    SenderType,
    MessageType,
)
from app.models.user import UserRole
from app.schemas.chat import (
    ChatMessageCreateSchema,
    ChatMessageUpdateSchema,
    ChatMessageResponse,
)
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.doctor_repository import DoctorProfileRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _message_to_response(message: ChatMessageInDB) -> ChatMessageResponse:
    from app.schemas.chat import ChatMessageMetadata
    # Ensure metadata is correctly mapped to ChatMessageMetadata schema
    meta = ChatMessageMetadata(**message.metadata) if isinstance(message.metadata, dict) else message.metadata
    return ChatMessageResponse(
        id=message.id,
        session_id=message.session_id,
        sender_type=message.sender_type,
        sender_id=message.sender_id,
        message=message.message,
        message_type=message.message_type,
        metadata=meta,
        created_at=message.created_at,
    )


class ChatMessageService(BaseService[ChatMessageInDB, ChatMessageCreate, ChatMessageUpdate]):
    """Service layer for chat message operations"""

    def __init__(
        self,
        chat_message_repository: ChatMessageRepository,
        chat_session_repository: ChatSessionRepository,
        user_repository: UserRepository,
        doctor_profile_repository: Optional[DoctorProfileRepository] = None,
    ):
        super().__init__()
        self.chat_message_repository = chat_message_repository
        self.chat_session_repository = chat_session_repository
        self.user_repository = user_repository
        self.doctor_profile_repository = doctor_profile_repository

    async def create_message(
        self,
        schema: ChatMessageCreateSchema,
    ) -> ChatMessageInDB:
        """Create a new chat message record after validating session and sender existence"""
        # Validate session exists
        session = await self.chat_session_repository.get(schema.session_id)
        if not session:
            raise ValueError(f"Chat session with ID {schema.session_id} does not exist")

        # Validate sender exists (Optional check depending on SenderType)
        if schema.sender_type == SenderType.PATIENT:
            patient = await self.user_repository.get(schema.sender_id)
            if not patient:
                raise ValueError(f"Patient user with ID {schema.sender_id} does not exist")
            if patient.role != UserRole.PATIENT:
                raise ValueError(f"Sender with ID {schema.sender_id} is not a patient")
        elif schema.sender_type == SenderType.DOCTOR:
            # Try user lookup first
            doctor_user = await self.user_repository.get(schema.sender_id)
            if doctor_user:
                if doctor_user.role != UserRole.DOCTOR:
                    raise ValueError(f"Sender user with ID {schema.sender_id} is not a doctor")
            elif self.doctor_profile_repository:
                # If not user ID, check doctor profile ID
                doctor_profile = await self.doctor_profile_repository.get(schema.sender_id)
                if not doctor_profile:
                    raise ValueError(f"Doctor sender with ID {schema.sender_id} does not exist")
            else:
                raise ValueError(f"Doctor sender with ID {schema.sender_id} does not exist")

        now = utc_now()
        message_create = ChatMessageCreate(
            session_id=schema.session_id,
            sender_type=schema.sender_type,
            sender_id=schema.sender_id,
            message=schema.message,
            message_type=schema.message_type,
            metadata=schema.metadata.model_dump(exclude_unset=True) if schema.metadata else {},
        )

        doc_dict = message_create.model_dump()
        doc_dict["created_at"] = now

        result = await self.chat_message_repository.collection.insert_one(doc_dict)
        created = await self.chat_message_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Chat message was inserted but could not be retrieved")

        # Update the last_message_at timestamp of the chat session
        from app.models.chat import ChatSessionUpdate as ModelsChatSessionUpdate
        session_update = ModelsChatSessionUpdate(last_message_at=now)
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
    ) -> List[ChatMessageInDB]:
        """Fetch all messages for a given session ID"""
        return await self.chat_message_repository.get_by_session_id(session_id, limit=limit, skip=skip)

    async def list_latest_messages(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[ChatMessageInDB]:
        """Fetch the latest messages for a session"""
        return await self.chat_message_repository.get_latest_messages(session_id, limit=limit)

    async def update_message(
        self,
        message_id: str,
        schema: ChatMessageUpdateSchema,
    ) -> Optional[ChatMessageInDB]:
        """Update an existing chat message"""
        update = ChatMessageUpdate(**schema.model_dump(exclude_unset=True))
        return await self.chat_message_repository.update(message_id, update)

    async def delete_message(self, message_id: str) -> bool:
        """Permanently delete a chat message record"""
        return await self.chat_message_repository.delete(message_id)

    def to_response(self, message: ChatMessageInDB) -> ChatMessageResponse:
        """Convert internal model to API response"""
        return _message_to_response(message)
