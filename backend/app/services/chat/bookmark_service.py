"""
Nura - Bookmark Service
Manages creation, removal, and listing of bookmarked message logs
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.models.bookmark import BookmarkCreate
from app.repositories.bookmark_repository import BookmarkRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.schemas.chat import BookmarkResponse

logger = logging.getLogger(__name__)


class BookmarkService:
    """Manages chat message bookmarks for patients"""

    def __init__(
        self,
        bookmark_repository: BookmarkRepository,
        chat_message_repository: ChatMessageRepository,
        chat_session_repository: ChatSessionRepository
    ):
        self.bookmark_repository = bookmark_repository
        self.chat_message_repository = chat_message_repository
        self.chat_session_repository = chat_session_repository

    async def add_bookmark(self, patient_id: str, message_id: str) -> BookmarkResponse:
        """Create a bookmark for a message"""
        # Validate message exists and belongs to the patient
        msg = await self.chat_message_repository.get(message_id)
        if not msg or msg.deleted:
            raise ValueError("Message not found or has been deleted")
        if msg.patient_id != patient_id:
            raise PermissionError("Access forbidden to this message")

        # Check if already bookmarked
        existing = await self.bookmark_repository.get_by_user_and_message(patient_id, message_id)
        if existing:
            return BookmarkResponse(
                id=existing.id,
                message_id=existing.message_id,
                session_id=existing.session_id,
                patient_id=existing.patient_id,
                bookmarked_at=existing.created_at,
                message_content=msg.content,
                message_role=msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            )

        bookmark_in = BookmarkCreate(
            patient_id=patient_id,
            message_id=message_id,
            session_id=msg.session_id
        )
        created = await self.bookmark_repository.create(bookmark_in)
        return BookmarkResponse(
            id=created.id,
            message_id=created.message_id,
            session_id=created.session_id,
            patient_id=created.patient_id,
            bookmarked_at=created.created_at,
            message_content=msg.content,
            message_role=msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        )

    async def remove_bookmark(self, patient_id: str, message_id: str) -> bool:
        """Deletes a bookmark by message identifier"""
        existing = await self.bookmark_repository.get_by_user_and_message(patient_id, message_id)
        if not existing:
            return False
        await self.bookmark_repository.collection.delete_one({"_id": ObjectId(existing.id) if ObjectId.is_valid(existing.id) else existing.id})
        return True

    async def get_bookmarks(self, patient_id: str) -> List[BookmarkResponse]:
        """Fetch all bookmarked messages for a patient"""
        bookmarks = await self.bookmark_repository.list_by_patient_id(patient_id)
        response_list: List[BookmarkResponse] = []
        for b in bookmarks:
            msg = await self.chat_message_repository.get(b.message_id)
            if msg and not msg.deleted:
                response_list.append(
                    BookmarkResponse(
                        id=b.id,
                        message_id=b.message_id,
                        session_id=b.session_id,
                        patient_id=b.patient_id,
                        bookmarked_at=b.created_at,
                        message_content=msg.content,
                        message_role=msg.role.value if hasattr(msg.role, "value") else str(msg.role)
                    )
                )
        return response_list
from bson import ObjectId
