"""
Nura - OTP Repository
MongoDB repository for OTP verification operations
"""

from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models import OTPVerificationCreate, OTPVerificationInDB, OTPPurpose
from app.repositories.base import BaseRepository, _to_model


class OTPRepository(BaseRepository[OTPVerificationInDB, OTPVerificationCreate, dict]):
    """OTP verification repository."""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, OTPVerificationInDB)

    async def create_otp(self, otp_create: OTPVerificationCreate) -> OTPVerificationInDB:
        """Persist a new OTP record."""
        return await self.create(otp_create)

    async def get_latest(self, email: str, purpose: OTPPurpose) -> Optional[OTPVerificationInDB]:
        """Return the most-recent valid (non-verified, non-expired) OTP."""
        now = datetime.now(timezone.utc)
        cursor = self.collection.find(
            {
                "email": email.lower().strip(),
                "purpose": purpose,
                "verified": False,
                "expires_at": {"$gt": now},
            }
        ).sort("created_at", -1).limit(1)

        docs = await cursor.to_list(length=1)
        if docs:
            return _to_model(self.model_class, docs[0])
        return None

    async def mark_verified(self, otp_id: str) -> Optional[OTPVerificationInDB]:
        """Mark a specific OTP document as verified."""
        result = await self.collection.update_one(
            {"_id": ObjectId(otp_id)},
            {"$set": {"verified": True, "updated_at": datetime.now(timezone.utc)}},
        )
        if result.modified_count:
            return await self.get(otp_id)
        return None

    async def invalidate(self, email: str, purpose: OTPPurpose) -> int:
        """Mark all pending OTPs for an email+purpose as verified (prevents reuse).
        Returns the count of documents updated.
        """
        result = await self.collection.update_many(
            {"email": email.lower().strip(), "purpose": purpose, "verified": False},
            {"$set": {"verified": True, "updated_at": datetime.now(timezone.utc)}},
        )
        return result.modified_count

    async def verify_otp(
        self, email: str, otp: str, purpose: OTPPurpose
    ) -> Optional[OTPVerificationInDB]:
        """Atomically verify an OTP: find it, mark it verified, return the updated model.

        Returns None if the OTP is not found, already verified, or expired.
        """
        now = datetime.now(timezone.utc)
        otp_doc = await self.collection.find_one(
            {
                "email": email.lower().strip(),
                "otp": otp,
                "purpose": purpose,
                "verified": False,
                "expires_at": {"$gt": now},
            }
        )

        if not otp_doc:
            return None

        result = await self.collection.update_one(
            {"_id": otp_doc["_id"]},
            {"$set": {"verified": True, "updated_at": now}},
        )

        if result.modified_count:
            otp_doc["verified"] = True
            otp_doc["updated_at"] = now
            return _to_model(self.model_class, otp_doc)

        return None

    async def cleanup_expired_otps(self) -> int:
        """Delete all expired OTP records. Returns the count deleted."""
        result = await self.collection.delete_many(
            {"expires_at": {"$lt": datetime.now(timezone.utc)}}
        )
        return result.deleted_count
