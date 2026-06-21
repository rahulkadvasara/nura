"""
Nura - Chat Message Repository
MongoDB repository for chat_messages collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.chat import ChatMessageCreate, ChatMessageUpdate, ChatMessageInDB
from app.repositories.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessageInDB, ChatMessageCreate, ChatMessageUpdate]):
    """Repository for chat_messages collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, ChatMessageInDB)

    async def get_by_id(self, id: str) -> Optional[ChatMessageInDB]:
        """Fetch a chat message by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[ChatMessageInDB]:
        """List all chat messages"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_session_id(self, session_id: str, limit: int = 100, skip: int = 0) -> List[ChatMessageInDB]:
        """Fetch all messages for a given session ID"""
        return await self.get_many({"session_id": session_id}, limit=limit, skip=skip)

    async def get_latest_messages(self, session_id: str, limit: int = 50) -> List[ChatMessageInDB]:
        """Fetch the latest messages for a session, ordered by created_at descending"""
        cursor = self.collection.find({"session_id": session_id}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        # Convert and return in chronological (ascending) order
        results = [ChatMessageInDB.from_mongo(doc) for doc in docs]
        results.reverse()
        return results
