"""
Nura - Chat Session Repository
MongoDB repository for chat_sessions collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.chat import ChatSessionCreate, ChatSessionUpdate, ChatSessionInDB
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSessionInDB, ChatSessionCreate, ChatSessionUpdate]):
    """Repository for chat_sessions collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, ChatSessionInDB)

    async def get_by_id(self, id: str) -> Optional[ChatSessionInDB]:
        """Fetch a chat session by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[ChatSessionInDB]:
        """List all chat sessions"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_patient_id(self, patient_id: str, limit: int = 100, skip: int = 0) -> List[ChatSessionInDB]:
        """Fetch all chat sessions for a given patient"""
        return await self.get_many({"patient_id": patient_id}, limit=limit, skip=skip)

    async def get_active_sessions(self, patient_id: Optional[str] = None, limit: int = 100, skip: int = 0) -> List[ChatSessionInDB]:
        """Fetch all active chat sessions, optionally filtered by patient ID"""
        query = {"active": True}
        if patient_id:
            query["patient_id"] = patient_id
        return await self.get_many(query, limit=limit, skip=skip)
