"""
Nura - Bookmark Repository
MongoDB repository for chat_bookmarks collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.bookmark import BookmarkInDB, BookmarkCreate, BookmarkUpdate
from app.repositories.base import BaseRepository, _to_model


class BookmarkRepository(BaseRepository[BookmarkInDB, BookmarkCreate, BookmarkUpdate]):
    """Repository for chat_bookmarks collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, BookmarkInDB)

    async def get_by_user_and_message(self, patient_id: str, message_id: str) -> Optional[BookmarkInDB]:
        """Fetch bookmark by user and message identifier"""
        doc = await self.collection.find_one({
            "patient_id": patient_id,
            "message_id": message_id
        })
        if doc:
            return _to_model(self.model_class, doc)
        return None

    async def list_by_patient_id(self, patient_id: str) -> List[BookmarkInDB]:
        """List bookmarks for a specific patient"""
        cursor = self.collection.find({"patient_id": patient_id})
        docs = await cursor.to_list(length=100)
        return [_to_model(self.model_class, doc) for doc in docs]
