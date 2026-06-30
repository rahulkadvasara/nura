"""
Nura - Chat Session Repository
MongoDB repository for chat_sessions collection
"""

from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.chat import ChatSessionCreate, ChatSessionUpdate, ChatSessionInDB, SessionStatus
from app.repositories.base import BaseRepository, _to_model


class ChatSessionRepository(BaseRepository[ChatSessionInDB, ChatSessionCreate, ChatSessionUpdate]):
    """Repository for chat_sessions collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, ChatSessionInDB)

    async def get_by_id(self, id: str) -> Optional[ChatSessionInDB]:
        """Fetch a chat session by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[ChatSessionInDB]:
        """List all chat sessions, excluding DELETED ones"""
        cursor = self.collection.find({"status": {"$ne": SessionStatus.DELETED}}).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [_to_model(self.model_class, doc) for doc in docs]

    async def get_by_patient_id(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
        include_archived: bool = True
    ) -> List[ChatSessionInDB]:
        """Fetch all non-deleted chat sessions for a patient, ordered by pinned first, then newest first"""
        query: Dict[str, Any] = {
            "patient_id": patient_id,
            "status": {"$ne": SessionStatus.DELETED}
        }
        if not include_archived:
            query["status"] = SessionStatus.ACTIVE

        cursor = (
            self.collection.find(query)
            .sort([("pinned", -1), ("last_message_at", -1), ("created_at", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [_to_model(self.model_class, doc) for doc in docs]

    async def get_active_sessions(
        self,
        patient_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[ChatSessionInDB]:
        """Fetch all active chat sessions, optionally filtered by patient ID"""
        query: Dict[str, Any] = {"status": SessionStatus.ACTIVE}
        if patient_id:
            query["patient_id"] = patient_id
        
        cursor = (
            self.collection.find(query)
            .sort([("pinned", -1), ("last_message_at", -1), ("created_at", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [_to_model(self.model_class, doc) for doc in docs]
