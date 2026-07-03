"""
Nura - Chat Bookmark Model
MongoDB document model for bookmarking important messages
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class BookmarkBase(BaseModel):
    """Shared fields for ChatBookmark models"""
    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(..., description="User ID of the patient bookmarking the message")
    message_id: str = Field(..., description="ID of the message bookmarked")
    session_id: str = Field(..., description="ID of the chat session containing the message")


class BookmarkCreate(BookmarkBase):
    """Model used to insert a new bookmark"""
    pass


class BookmarkUpdate(BaseModel):
    """Model used to update a bookmark (empty placeholders)"""
    pass


class BookmarkInDB(BookmarkBase):
    """Database model representation of a bookmark"""
    id: str = Field(..., description="Bookmark Document ID")
    created_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def from_mongo(cls, data: dict) -> "BookmarkInDB":
        """Factory method to convert MongoDB dict into Pydantic model"""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
