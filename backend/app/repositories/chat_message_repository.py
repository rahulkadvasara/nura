"""
Nura - Chat Message Repository
MongoDB repository for chat_messages collection
"""

from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.chat import ChatMessageCreate, ChatMessageUpdate, ChatMessageInDB
from app.repositories.base import BaseRepository, _to_model


class ChatMessageRepository(BaseRepository[ChatMessageInDB, ChatMessageCreate, ChatMessageUpdate]):
    """Repository for chat_messages collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, ChatMessageInDB)

    async def get_by_id(self, id: str) -> Optional[ChatMessageInDB]:
        """Fetch a chat message by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[ChatMessageInDB]:
        """List all non-deleted chat messages"""
        cursor = self.collection.find({"deleted": {"$ne": True}}).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [_to_model(self.model_class, doc) for doc in docs]

    async def get_by_session_id(
        self,
        session_id: str,
        limit: int = 100,
        skip: int = 0,
        include_deleted: bool = False
    ) -> List[ChatMessageInDB]:
        """Fetch all messages for a given session ID, sorted chronologically (ascending)"""
        query: Dict[str, Any] = {"session_id": session_id}
        if not include_deleted:
            query["deleted"] = {"$ne": True}
        
        cursor = self.collection.find(query).sort("created_at", 1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [_to_model(self.model_class, doc) for doc in docs]

    async def get_latest_messages(self, session_id: str, limit: int = 50) -> List[ChatMessageInDB]:
        """Fetch the latest messages for a session, ordered chronologically (ascending)"""
        cursor = self.collection.find({"session_id": session_id, "deleted": {"$ne": True}}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        results = [_to_model(self.model_class, doc) for doc in docs]
        results.reverse()
        return results
