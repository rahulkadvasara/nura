"""
Nura - Refresh Token Repository
MongoDB repository for refresh token operations
"""

from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models import RefreshTokenCreate, RefreshTokenInDB
from app.repositories.base import BaseRepository, _to_model


class RefreshTokenRepository(BaseRepository[RefreshTokenInDB, RefreshTokenCreate, dict]):
    """Refresh token repository."""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, RefreshTokenInDB)

    async def create_token(self, token_create: RefreshTokenCreate) -> RefreshTokenInDB:
        """Persist a new refresh token."""
        return await self.create(token_create)

    async def revoke_token(self, token_id: str) -> Optional[RefreshTokenInDB]:
        """Revoke a single refresh token by its ID."""
        result = await self.collection.update_one(
            {"_id": ObjectId(token_id)},
            {"$set": {"revoked": True, "updated_at": datetime.now(timezone.utc)}},
        )
        if result.modified_count:
            return await self.get(token_id)
        return None

    async def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke every active token for the given user. Returns count revoked."""
        now = datetime.now(timezone.utc)
        result = await self.collection.update_many(
            {"user_id": user_id, "revoked": False, "expires_at": {"$gt": now}},
            {"$set": {"revoked": True, "updated_at": now}},
        )
        return result.modified_count

    async def get_active(self, user_id: str) -> List[RefreshTokenInDB]:
        """Return all non-revoked, non-expired tokens for a user."""
        now = datetime.now(timezone.utc)
        cursor = self.collection.find(
            {"user_id": user_id, "revoked": False, "expires_at": {"$gt": now}}
        ).sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [_to_model(self.model_class, doc) for doc in docs]

    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshTokenInDB]:
        """Fetch a token record by its stored hash."""
        return await self.get_by_filter({"token_hash": token_hash})

    async def revoke_by_hash(self, token_hash: str) -> bool:
        """Find a token by hash and revoke it. Returns True on success."""
        token = await self.get_by_token_hash(token_hash)
        if token:
            return await self.revoke_token(token.id) is not None
        return False

    async def cleanup_expired_tokens(self) -> int:
        """Delete all expired tokens. Returns the count deleted."""
        result = await self.collection.delete_many(
            {"expires_at": {"$lt": datetime.now(timezone.utc)}}
        )
        return result.deleted_count

    async def get_all_by_user(self, user_id: str, limit: int = 100) -> List[RefreshTokenInDB]:
        """Fetch all refresh token sessions (active, revoked, expired) for a user, sorted newest first"""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [_to_model(self.model_class, doc) for doc in docs]

    async def update_last_activity(self, token_id: str) -> Optional[RefreshTokenInDB]:
        """Update the last activity timestamp for a single token."""
        result = await self.collection.update_one(
            {"_id": ObjectId(token_id)},
            {"$set": {"last_activity": datetime.now(timezone.utc)}},
        )
        return await self.get(token_id)

