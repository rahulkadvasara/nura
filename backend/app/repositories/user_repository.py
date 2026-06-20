"""
Nura - User Repository
MongoDB repository for user operations
"""

from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models import UserCreate, UserUpdate, UserInDB
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserInDB, UserCreate, UserUpdate]):
    """User repository with user-specific operations"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, UserInDB)

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email (case-insensitive via pre-normalised storage)."""
        return await self.get_by_filter({"email": email.lower().strip()})

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        return await self.get(user_id)

    async def verify_email(self, user_id: str) -> Optional[UserInDB]:
        """Mark a user's email as verified and return the updated document."""
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "email_verified": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count:
            return await self.get(user_id)
        return None

    async def exists_by_email(self, email: str) -> bool:
        """Return True if a user with the given email already exists."""
        return await self.exists({"email": email.lower().strip()})

    async def create_user(self, user_create: UserCreate) -> UserInDB:
        """Persist a new user document.

        Password hashing must be performed in the service layer before
        calling this method.
        """
        return await self.create(user_create)
