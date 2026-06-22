"""
Nura - Doctor Services
Business logic for doctor_profiles, doctor_documents, and doctor_availability
"""

from datetime import datetime, timezone
from typing import List, Optional

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
from app.repositories.doctor_repository import (
    DoctorProfileRepository,
    DoctorDocumentRepository,
    DoctorAvailabilityRepository,
)
from app.schemas.doctor import (
    DoctorProfileCreateSchema,
    DoctorProfileUpdateSchema,
    DoctorProfileResponse,
    DoctorDocumentCreateSchema,
    DoctorDocumentUpdateSchema,
    DoctorDocumentResponse,
    DoctorAvailabilityCreateSchema,
    DoctorAvailabilityUpdateSchema,
    DoctorAvailabilityResponse,
)
from app.services.base import BaseService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _profile_to_response(profile: DoctorProfileInDB) -> DoctorProfileResponse:
    """Convert a DoctorProfileInDB to a DoctorProfileResponse."""
    return DoctorProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        specialization=profile.specialization,
        qualifications=profile.qualifications,
        experience_years=profile.experience_years,
        consultation_fee=profile.consultation_fee,
        bio=profile.bio,
        languages=profile.languages,
        hospital=profile.hospital,
        license_number=profile.license_number,
        education=profile.education,
        profile_status=profile.profile_status,
        average_rating=profile.average_rating,
        total_reviews=profile.total_reviews,
        rejection_reason=profile.rejection_reason,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _document_to_response(doc: DoctorDocumentInDB) -> DoctorDocumentResponse:
    """Convert a DoctorDocumentInDB to a DoctorDocumentResponse."""
    return DoctorDocumentResponse(
        id=doc.id,
        doctor_id=doc.doctor_id,
        document_type=doc.document_type,
        document_url=doc.document_url,
        verification_status=doc.verification_status,
        uploaded_at=doc.uploaded_at,
        verified_at=doc.verified_at,
        verified_by=doc.verified_by,
    )


def _availability_to_response(avail: DoctorAvailabilityInDB) -> DoctorAvailabilityResponse:
    """Convert a DoctorAvailabilityInDB to a DoctorAvailabilityResponse."""
    return DoctorAvailabilityResponse(
        id=avail.id,
        doctor_id=avail.doctor_id,
        day_of_week=avail.day_of_week,
        start_time=avail.start_time,
        end_time=avail.end_time,
        slot_duration=avail.slot_duration,
        active=avail.active,
    )


# ---------------------------------------------------------------------------
# DoctorProfileService
# ---------------------------------------------------------------------------

class DoctorProfileService(BaseService[DoctorProfileInDB, DoctorProfileCreate, DoctorProfileUpdate]):
    """Service layer for doctor profile operations."""

    def __init__(self, profile_repository: DoctorProfileRepository):
        super().__init__()
        self.profile_repository = profile_repository

    # ---- Create ------------------------------------------------------------

    async def create_profile(
        self,
        user_id: str,
        schema: DoctorProfileCreateSchema,
    ) -> DoctorProfileInDB:
        """Create a new doctor profile for the given user.

        Raises:
            ValueError: If a profile already exists for the user.
        """
        if await self.profile_repository.exists_for_user(user_id):
            raise ValueError(f"A doctor profile already exists for user {user_id}")

        now = datetime.now(timezone.utc)
        profile_create = DoctorProfileCreate(
            user_id=user_id,
            specialization=schema.specialization,
            qualifications=schema.qualifications,
            experience_years=schema.experience_years,
            consultation_fee=schema.consultation_fee,
            bio=schema.bio,
            languages=schema.languages,
            hospital=schema.hospital,
            license_number=schema.license_number,
            education=schema.education,
            profile_status=DoctorProfileStatus.PENDING,
            average_rating=0.0,
            total_reviews=0,
        )

        # Insert via raw collection to set timestamps explicitly
        doc_dict = profile_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.profile_repository.collection.insert_one(doc_dict)
        created = await self.profile_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Doctor profile was inserted but could not be retrieved")
        return DoctorProfileInDB.from_mongo(created)

    # ---- Read --------------------------------------------------------------

    async def get_profile_by_id(self, profile_id: str) -> Optional[DoctorProfileInDB]:
        """Fetch a doctor profile by its ID."""
        return await self.profile_repository.get(profile_id)

    async def get_profile_by_user_id(self, user_id: str) -> Optional[DoctorProfileInDB]:
        """Fetch the doctor profile associated with a user."""
        return await self.profile_repository.get_by_user_id(user_id)

    async def list_profiles(self, limit: int = 100, skip: int = 0) -> List[DoctorProfileInDB]:
        """List all doctor profiles."""
        return await self.profile_repository.list_profiles(limit=limit, skip=skip)

    async def list_verified_doctors(self, limit: int = 100, skip: int = 0) -> List[DoctorProfileInDB]:
        """List only verified doctor profiles."""
        return await self.profile_repository.get_verified_doctors(limit=limit, skip=skip)

    async def list_by_status(
        self,
        status: DoctorProfileStatus,
        limit: int = 100,
        skip: int = 0,
    ) -> List[DoctorProfileInDB]:
        """List doctor profiles filtered by verification status."""
        return await self.profile_repository.get_by_status(status, limit=limit, skip=skip)

    # ---- Update ------------------------------------------------------------

    async def update_profile(
        self,
        profile_id: str,
        schema: DoctorProfileUpdateSchema,
    ) -> Optional[DoctorProfileInDB]:
        """Update non-status fields of a doctor profile."""
        update = DoctorProfileUpdate(
            specialization=schema.specialization,
            qualifications=schema.qualifications,
            experience_years=schema.experience_years,
            consultation_fee=schema.consultation_fee,
            bio=schema.bio,
            languages=schema.languages,
            hospital=schema.hospital,
            license_number=schema.license_number,
            education=schema.education,
        )
        return await self.profile_repository.update(profile_id, update)

    async def verify_profile(self, profile_id: str) -> Optional[DoctorProfileInDB]:
        """Mark a doctor profile as verified (admin action)."""
        return await self.profile_repository.update_status(profile_id, DoctorProfileStatus.VERIFIED)

    async def reject_profile(self, profile_id: str, rejection_reason: Optional[str] = None) -> Optional[DoctorProfileInDB]:
        """Mark a doctor profile as rejected (admin action)."""
        return await self.profile_repository.update_status(profile_id, DoctorProfileStatus.REJECTED, rejection_reason)

    # ---- Delete ------------------------------------------------------------

    async def delete_profile(self, profile_id: str) -> bool:
        """Permanently delete a doctor profile."""
        return await self.profile_repository.delete(profile_id)

    # ---- Serialisation -----------------------------------------------------

    def to_response(self, profile: DoctorProfileInDB) -> DoctorProfileResponse:
        """Convert internal model to API response."""
        return _profile_to_response(profile)


# ---------------------------------------------------------------------------
# DoctorDocumentService
# ---------------------------------------------------------------------------

class DoctorDocumentService(BaseService[DoctorDocumentInDB, DoctorDocumentCreate, DoctorDocumentUpdate]):
    """Service layer for doctor document operations."""

    def __init__(self, document_repository: DoctorDocumentRepository):
        super().__init__()
        self.document_repository = document_repository

    # ---- Create ------------------------------------------------------------

    async def upload_document(
        self,
        doctor_id: str,
        schema: DoctorDocumentCreateSchema,
    ) -> DoctorDocumentInDB:
        """Record a new verification document upload for a doctor."""
        now = datetime.now(timezone.utc)
        doc_create = DoctorDocumentCreate(
            doctor_id=doctor_id,
            document_type=schema.document_type,
            document_url=schema.document_url,
            verification_status=DocumentVerificationStatus.PENDING,
            uploaded_at=now,
        )

        doc_dict = doc_create.model_dump()
        doc_dict["uploaded_at"] = now

        result = await self.document_repository.collection.insert_one(doc_dict)
        created = await self.document_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Doctor document was inserted but could not be retrieved")
        return DoctorDocumentInDB.from_mongo(created)

    # ---- Read --------------------------------------------------------------

    async def get_document_by_id(self, document_id: str) -> Optional[DoctorDocumentInDB]:
        """Fetch a single document by its ID."""
        return await self.document_repository.get(document_id)

    async def get_documents_by_doctor(self, doctor_id: str) -> List[DoctorDocumentInDB]:
        """Fetch all documents for a given doctor."""
        return await self.document_repository.get_by_doctor_id(doctor_id)

    async def list_pending_documents(
        self,
        limit: int = 100,
        skip: int = 0,
    ) -> List[DoctorDocumentInDB]:
        """List all documents pending admin review."""
        return await self.document_repository.get_pending_documents(limit=limit, skip=skip)

    async def list_documents(self, limit: int = 100, skip: int = 0) -> List[DoctorDocumentInDB]:
        """List all documents (unfiltered)."""
        return await self.document_repository.list_documents(limit=limit, skip=skip)

    # ---- Update ------------------------------------------------------------

    async def update_document(
        self,
        document_id: str,
        schema: DoctorDocumentUpdateSchema,
    ) -> Optional[DoctorDocumentInDB]:
        """Update a document's metadata (does not change verification status)."""
        update = DoctorDocumentUpdate(
            document_type=schema.document_type,
            document_url=schema.document_url,
        )
        return await self.document_repository.update(document_id, update)

    async def approve_document(
        self,
        document_id: str,
        admin_user_id: str,
    ) -> Optional[DoctorDocumentInDB]:
        """Approve a document (admin action)."""
        return await self.document_repository.approve_document(document_id, admin_user_id)

    async def reject_document(
        self,
        document_id: str,
        admin_user_id: str,
    ) -> Optional[DoctorDocumentInDB]:
        """Reject a document (admin action)."""
        return await self.document_repository.reject_document(document_id, admin_user_id)

    # ---- Delete ------------------------------------------------------------

    async def delete_document(self, document_id: str) -> bool:
        """Permanently delete a document record."""
        return await self.document_repository.delete(document_id)

    # ---- Serialisation -----------------------------------------------------

    def to_response(self, doc: DoctorDocumentInDB) -> DoctorDocumentResponse:
        """Convert internal model to API response."""
        return _document_to_response(doc)


# ---------------------------------------------------------------------------
# DoctorAvailabilityService
# ---------------------------------------------------------------------------

class DoctorAvailabilityService(
    BaseService[DoctorAvailabilityInDB, DoctorAvailabilityCreate, DoctorAvailabilityUpdate]
):
    """Service layer for doctor availability operations."""

    def __init__(self, availability_repository: DoctorAvailabilityRepository):
        super().__init__()
        self.availability_repository = availability_repository

    # ---- Validation --------------------------------------------------------

    @staticmethod
    def _validate_time_range(start_time: str, end_time: str) -> None:
        """Ensure start_time is strictly before end_time.

        Args:
            start_time: Time string in HH:MM format.
            end_time:   Time string in HH:MM format.

        Raises:
            ValueError: If end_time is not after start_time.
        """
        start_h, start_m = map(int, start_time.split(":"))
        end_h, end_m = map(int, end_time.split(":"))
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        if end_minutes <= start_minutes:
            raise ValueError(
                f"end_time '{end_time}' must be after start_time '{start_time}'"
            )

    # ---- Create ------------------------------------------------------------

    async def create_availability(
        self,
        doctor_id: str,
        schema: DoctorAvailabilityCreateSchema,
    ) -> DoctorAvailabilityInDB:
        """Create a new availability slot for a doctor.

        Raises:
            ValueError: If the time range is invalid.
        """
        self._validate_time_range(schema.start_time, schema.end_time)

        avail_create = DoctorAvailabilityCreate(
            doctor_id=doctor_id,
            day_of_week=schema.day_of_week,
            start_time=schema.start_time,
            end_time=schema.end_time,
            slot_duration=schema.slot_duration,
            active=schema.active,
        )
        return await self.availability_repository.create(avail_create)

    # ---- Read --------------------------------------------------------------

    async def get_availability_by_id(self, availability_id: str) -> Optional[DoctorAvailabilityInDB]:
        """Fetch a single availability slot by its ID."""
        return await self.availability_repository.get(availability_id)

    async def get_availability_by_doctor(self, doctor_id: str) -> List[DoctorAvailabilityInDB]:
        """Fetch all availability slots for a given doctor."""
        return await self.availability_repository.get_by_doctor_id(doctor_id)

    async def get_active_availability(self, doctor_id: str) -> List[DoctorAvailabilityInDB]:
        """Fetch only active availability slots for a given doctor."""
        return await self.availability_repository.get_active_by_doctor_id(doctor_id)

    async def get_availability_by_day(
        self,
        doctor_id: str,
        day_of_week: DayOfWeek,
    ) -> List[DoctorAvailabilityInDB]:
        """Fetch availability slots for a doctor on a specific day."""
        return await self.availability_repository.get_by_doctor_and_day(doctor_id, day_of_week)

    async def list_availability(self, limit: int = 100, skip: int = 0) -> List[DoctorAvailabilityInDB]:
        """List all availability records (unfiltered)."""
        return await self.availability_repository.list_availability(limit=limit, skip=skip)

    # ---- Update ------------------------------------------------------------

    async def update_availability(
        self,
        availability_id: str,
        schema: DoctorAvailabilityUpdateSchema,
    ) -> Optional[DoctorAvailabilityInDB]:
        """Update an existing availability slot.

        Raises:
            ValueError: If the resulting time range is invalid.
        """
        # Resolve final start/end times for validation when only one is provided
        existing = await self.get_availability_by_id(availability_id)
        if existing:
            start = schema.start_time or existing.start_time
            end = schema.end_time or existing.end_time
            self._validate_time_range(start, end)

        update = DoctorAvailabilityUpdate(
            day_of_week=schema.day_of_week,
            start_time=schema.start_time,
            end_time=schema.end_time,
            slot_duration=schema.slot_duration,
            active=schema.active,
        )
        return await self.availability_repository.update(availability_id, update)

    async def deactivate_availability(self, availability_id: str) -> Optional[DoctorAvailabilityInDB]:
        """Mark a specific slot as inactive."""
        return await self.availability_repository.set_active(availability_id, False)

    async def activate_availability(self, availability_id: str) -> Optional[DoctorAvailabilityInDB]:
        """Mark a specific slot as active."""
        return await self.availability_repository.set_active(availability_id, True)

    # ---- Delete ------------------------------------------------------------

    async def delete_availability(self, availability_id: str) -> bool:
        """Permanently delete an availability slot."""
        return await self.availability_repository.delete(availability_id)

    # ---- Serialisation -----------------------------------------------------

    def to_response(self, avail: DoctorAvailabilityInDB) -> DoctorAvailabilityResponse:
        """Convert internal model to API response."""
        return _availability_to_response(avail)
