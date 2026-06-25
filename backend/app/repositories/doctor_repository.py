"""
Nura - Doctor Repositories
MongoDB repositories for doctor_profiles, doctor_documents, and doctor_availability collections
"""

from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.doctor import (
    DoctorProfileCreate,
    DoctorProfileUpdate,
    DoctorProfileInDB,
    DoctorProfileStatus,
    DoctorDocumentCreate,
    DoctorDocumentUpdate,
    DoctorDocumentInDB,
    DocumentVerificationStatus,
    DoctorAvailabilityCreate,
    DoctorAvailabilityUpdate,
    DoctorAvailabilityInDB,
    DayOfWeek,
)
from app.repositories.base import BaseRepository


# ---------------------------------------------------------------------------
# DoctorProfileRepository
# ---------------------------------------------------------------------------

class DoctorProfileRepository(BaseRepository[DoctorProfileInDB, DoctorProfileCreate, DoctorProfileUpdate]):
    """Repository for doctor_profiles collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, DoctorProfileInDB)

    # ---- Lookups -----------------------------------------------------------

    async def get_by_user_id(self, user_id: str) -> Optional[DoctorProfileInDB]:
        """Return the doctor profile that belongs to a given user."""
        return await self.get_by_filter({"user_id": user_id})

    async def get_by_status(
        self,
        status: DoctorProfileStatus,
        limit: int = 100,
        skip: int = 0,
    ) -> List[DoctorProfileInDB]:
        """Return all profiles with the given verification status."""
        return await self.get_many({"profile_status": status.value}, limit=limit, skip=skip)

    async def get_verified_doctors(self, limit: int = 100, skip: int = 0) -> List[DoctorProfileInDB]:
        """Return all verified doctor profiles."""
        return await self.get_by_status(DoctorProfileStatus.VERIFIED, limit=limit, skip=skip)

    async def exists_for_user(self, user_id: str) -> bool:
        """Return True if a profile already exists for the given user."""
        return await self.exists({"user_id": user_id})

    # ---- Status updates ----------------------------------------------------

    async def update_status(
        self,
        profile_id: str,
        new_status: DoctorProfileStatus,
        rejection_reason: Optional[str] = None,
    ) -> Optional[DoctorProfileInDB]:
        """Change the verification status of a doctor profile."""
        update_dict = {
            "profile_status": new_status.value,
            "updated_at": datetime.now(timezone.utc),
        }
        if new_status == DoctorProfileStatus.REJECTED:
            update_dict["rejection_reason"] = rejection_reason
        else:
            update_dict["rejection_reason"] = None

        result = await self.collection.update_one(
            {"_id": ObjectId(profile_id)},
            {"$set": update_dict},
        )
        if result.matched_count:
            return await self.get(profile_id)
        return None

    async def update_rating(
        self,
        profile_id: str,
        average_rating: float,
        total_reviews: int,
    ) -> Optional[DoctorProfileInDB]:
        """Update the average rating and review count for a doctor."""
        result = await self.collection.update_one(
            {"_id": ObjectId(profile_id)},
            {
                "$set": {
                    "average_rating": average_rating,
                    "total_reviews": total_reviews,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count:
            return await self.get(profile_id)
        return None

    # ---- Convenience list --------------------------------------------------

    async def list_profiles(self, limit: int = 100, skip: int = 0) -> List[DoctorProfileInDB]:
        """Return all doctor profiles (unfiltered)."""
        return await self.get_many({}, limit=limit, skip=skip)


# ---------------------------------------------------------------------------
# DoctorDocumentRepository
# ---------------------------------------------------------------------------

class DoctorDocumentRepository(BaseRepository[DoctorDocumentInDB, DoctorDocumentCreate, DoctorDocumentUpdate]):
    """Repository for doctor_documents collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, DoctorDocumentInDB)

    # ---- Lookups -----------------------------------------------------------

    async def get_by_doctor_id(self, doctor_id: str) -> List[DoctorDocumentInDB]:
        """Return all documents uploaded by a given doctor."""
        return await self.get_many({"doctor_id": doctor_id})

    async def get_pending_documents(self, limit: int = 100, skip: int = 0) -> List[DoctorDocumentInDB]:
        """Return all documents awaiting admin review."""
        return await self.get_many(
            {"verification_status": DocumentVerificationStatus.PENDING.value},
            limit=limit,
            skip=skip,
        )

    async def get_by_doctor_and_status(
        self,
        doctor_id: str,
        status: DocumentVerificationStatus,
    ) -> List[DoctorDocumentInDB]:
        """Return a doctor's documents filtered by verification status."""
        return await self.get_many({"doctor_id": doctor_id, "verification_status": status.value})

    # ---- Status updates ----------------------------------------------------

    async def approve_document(
        self,
        document_id: str,
        verified_by: str,
    ) -> Optional[DoctorDocumentInDB]:
        """Mark a document as approved by an admin."""
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {
                "$set": {
                    "verification_status": DocumentVerificationStatus.APPROVED.value,
                    "verified_at": now,
                    "verified_by": verified_by,
                }
            },
        )
        if result.modified_count:
            return await self.get(document_id)
        return None

    async def reject_document(
        self,
        document_id: str,
        verified_by: str,
    ) -> Optional[DoctorDocumentInDB]:
        """Mark a document as rejected by an admin."""
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {
                "$set": {
                    "verification_status": DocumentVerificationStatus.REJECTED.value,
                    "verified_at": now,
                    "verified_by": verified_by,
                }
            },
        )
        if result.modified_count:
            return await self.get(document_id)
        return None

    # ---- Convenience list --------------------------------------------------

    async def list_documents(self, limit: int = 100, skip: int = 0) -> List[DoctorDocumentInDB]:
        """Return all documents (unfiltered)."""
        return await self.get_many({}, limit=limit, skip=skip)


# ---------------------------------------------------------------------------
# DoctorAvailabilityRepository
# ---------------------------------------------------------------------------

class DoctorAvailabilityRepository(
    BaseRepository[DoctorAvailabilityInDB, DoctorAvailabilityCreate, DoctorAvailabilityUpdate]
):
    """Repository for doctor_availability collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, DoctorAvailabilityInDB)

    # ---- Lookups -----------------------------------------------------------

    async def get_by_doctor_id(self, doctor_id: str) -> List[DoctorAvailabilityInDB]:
        """Return all availability records for a given doctor."""
        return await self.get_many({"doctor_id": doctor_id})

    async def get_active_by_doctor_id(self, doctor_id: str) -> List[DoctorAvailabilityInDB]:
        """Return only active availability records for a given doctor."""
        return await self.get_many({"doctor_id": doctor_id, "active": {"$ne": False}})

    async def get_by_doctor_and_day(
        self,
        doctor_id: str,
        day_of_week: DayOfWeek,
    ) -> List[DoctorAvailabilityInDB]:
        """Return availability records for a specific doctor on a given day."""
        return await self.get_many({"doctor_id": doctor_id, "day_of_week": day_of_week.value})

    # ---- Status toggle -----------------------------------------------------

    async def set_active(
        self,
        availability_id: str,
        active: bool,
    ) -> Optional[DoctorAvailabilityInDB]:
        """Enable or disable an availability slot."""
        result = await self.collection.update_one(
            {"_id": ObjectId(availability_id)},
            {"$set": {"active": active}},
        )
        if result.modified_count:
            return await self.get(availability_id)
        return None

    async def deactivate_all_for_doctor(self, doctor_id: str) -> int:
        """Deactivate all availability slots for a given doctor. Returns updated count."""
        result = await self.collection.update_many(
            {"doctor_id": doctor_id},
            {"$set": {"active": False}},
        )
        return result.modified_count

    # ---- Convenience list --------------------------------------------------

    async def list_availability(self, limit: int = 100, skip: int = 0) -> List[DoctorAvailabilityInDB]:
        """Return all availability records (unfiltered)."""
        return await self.get_many({}, limit=limit, skip=skip)
