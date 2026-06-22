"""
Nura - Doctor Repositories Tests
Unit tests for DoctorProfileRepository, DoctorDocumentRepository,
and DoctorAvailabilityRepository using mocked MongoDB collections.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from app.models.doctor import (
    DoctorProfileCreate,
    DoctorProfileUpdate,
    DoctorProfileInDB,
    DoctorProfileStatus,
    DoctorDocumentCreate,
    DoctorDocumentUpdate,
    DoctorDocumentInDB,
    DocumentVerificationStatus,
    DocumentType,
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


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_profile_doc(
    profile_id: str = "507f1f77bcf86cd799439010",
    user_id: str = "507f1f77bcf86cd799439001",
    status: str = "pending",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(profile_id),
        "user_id": user_id,
        "specialization": "Cardiology",
        "qualifications": ["MBBS", "MD"],
        "experience_years": 10,
        "consultation_fee": 500.0,
        "bio": "Expert cardiologist.",
        "languages": ["English"],
        "hospital": "City Heart Hospital",
        "license_number": "MH-12345",
        "profile_status": status,
        "average_rating": 0.0,
        "total_reviews": 0,
        "created_at": now,
        "updated_at": now,
    }


def make_document_doc(
    doc_id: str = "507f1f77bcf86cd799439020",
    doctor_id: str = "507f1f77bcf86cd799439010",
    status: str = "pending",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(doc_id),
        "doctor_id": doctor_id,
        "document_type": "license",
        "document_url": "https://example.com/license.pdf",
        "verification_status": status,
        "uploaded_at": now,
        "verified_at": None,
        "verified_by": None,
    }


def make_availability_doc(
    avail_id: str = "507f1f77bcf86cd799439030",
    doctor_id: str = "507f1f77bcf86cd799439010",
    active: bool = True,
) -> dict:
    return {
        "_id": ObjectId(avail_id),
        "doctor_id": doctor_id,
        "date": "2026-06-22",
        "day_of_week": "monday",
        "start_time": "09:00",
        "end_time": "17:00",
        "slot_duration": 30,
        "active": active,
    }


def make_mock_collection(find_one_return=None, find_return=None, update_result=None):
    """Build a mock AsyncIOMotorCollection with common method stubs."""
    collection = MagicMock()

    # find_one
    collection.find_one = AsyncMock(return_value=find_one_return)

    # insert_one
    insert_result = MagicMock()
    insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439010")
    collection.insert_one = AsyncMock(return_value=insert_result)

    # update_one
    upd_result = MagicMock()
    upd_result.modified_count = 1 if update_result is None else update_result
    collection.update_one = AsyncMock(return_value=upd_result)

    # update_many
    collection.update_many = AsyncMock(return_value=upd_result)

    # delete_one
    del_result = MagicMock()
    del_result.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=del_result)

    # find / cursor chain
    cursor = MagicMock()
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=find_return or [])
    collection.find = MagicMock(return_value=cursor)

    # count_documents
    collection.count_documents = AsyncMock(return_value=0)

    return collection


# ===========================================================================
# DoctorProfileRepository tests
# ===========================================================================

class TestDoctorProfileRepository:

    @pytest.mark.asyncio
    async def test_create_profile(self):
        profile_doc = make_profile_doc()
        collection = make_mock_collection(find_one_return=profile_doc)

        repo = DoctorProfileRepository(collection)
        profile_create = DoctorProfileCreate(
            user_id="507f1f77bcf86cd799439001",
            specialization="Cardiology",
            qualifications=["MBBS"],
            experience_years=10,
            consultation_fee=500.0,
        )
        result = await repo.create(profile_create)

        assert isinstance(result, DoctorProfileInDB)
        assert result.specialization == "Cardiology"
        collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_profile(self):
        profile_doc = make_profile_doc()
        collection = make_mock_collection(find_one_return=profile_doc)

        repo = DoctorProfileRepository(collection)
        result = await repo.get("507f1f77bcf86cd799439010")

        assert result is not None
        assert result.id == "507f1f77bcf86cd799439010"

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self):
        collection = make_mock_collection(find_one_return=None)
        repo = DoctorProfileRepository(collection)
        result = await repo.get("507f1f77bcf86cd799439010")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_user_id(self):
        profile_doc = make_profile_doc()
        collection = make_mock_collection(find_one_return=profile_doc)

        repo = DoctorProfileRepository(collection)
        result = await repo.get_by_user_id("507f1f77bcf86cd799439001")

        assert result is not None
        assert result.user_id == "507f1f77bcf86cd799439001"

    @pytest.mark.asyncio
    async def test_update_profile(self):
        updated_doc = make_profile_doc()
        updated_doc["specialization"] = "Neurology"
        collection = make_mock_collection(find_one_return=updated_doc)

        repo = DoctorProfileRepository(collection)
        update = DoctorProfileUpdate(specialization="Neurology")
        result = await repo.update("507f1f77bcf86cd799439010", update)

        assert result is not None
        assert result.specialization == "Neurology"
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_profile(self):
        collection = make_mock_collection()
        repo = DoctorProfileRepository(collection)
        result = await repo.delete("507f1f77bcf86cd799439010")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_by_status(self):
        docs = [make_profile_doc(), make_profile_doc("507f1f77bcf86cd799439011")]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorProfileRepository(collection)
        results = await repo.get_by_status(DoctorProfileStatus.PENDING)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_verified_doctors(self):
        docs = [make_profile_doc(status="verified")]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorProfileRepository(collection)
        results = await repo.get_verified_doctors()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_update_status(self):
        profile_doc = make_profile_doc(status="verified")
        collection = make_mock_collection(find_one_return=profile_doc)

        repo = DoctorProfileRepository(collection)
        result = await repo.update_status("507f1f77bcf86cd799439010", DoctorProfileStatus.VERIFIED)

        assert result is not None
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_rating(self):
        profile_doc = make_profile_doc()
        profile_doc["average_rating"] = 4.5
        profile_doc["total_reviews"] = 10
        collection = make_mock_collection(find_one_return=profile_doc)

        repo = DoctorProfileRepository(collection)
        result = await repo.update_rating("507f1f77bcf86cd799439010", 4.5, 10)

        assert result is not None
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_for_user(self):
        collection = make_mock_collection()
        collection.count_documents = AsyncMock(return_value=1)

        repo = DoctorProfileRepository(collection)
        result = await repo.exists_for_user("507f1f77bcf86cd799439001")
        assert result is True

    @pytest.mark.asyncio
    async def test_list_profiles(self):
        docs = [make_profile_doc()]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorProfileRepository(collection)
        results = await repo.list_profiles()
        assert len(results) == 1


# ===========================================================================
# DoctorDocumentRepository tests
# ===========================================================================

class TestDoctorDocumentRepository:

    @pytest.mark.asyncio
    async def test_create_document(self):
        doc = make_document_doc()
        collection = make_mock_collection(find_one_return=doc)
        collection.insert_one.return_value.inserted_id = ObjectId("507f1f77bcf86cd799439020")

        repo = DoctorDocumentRepository(collection)
        doc_create = DoctorDocumentCreate(
            doctor_id="507f1f77bcf86cd799439010",
            document_type=DocumentType.LICENSE,
            document_url="https://example.com/license.pdf",
            verification_status=DocumentVerificationStatus.PENDING,
        )
        result = await repo.create(doc_create)

        assert isinstance(result, DoctorDocumentInDB)
        assert result.document_type == DocumentType.LICENSE

    @pytest.mark.asyncio
    async def test_get_document(self):
        doc = make_document_doc()
        collection = make_mock_collection(find_one_return=doc)

        repo = DoctorDocumentRepository(collection)
        result = await repo.get("507f1f77bcf86cd799439020")

        assert result is not None
        assert result.doctor_id == "507f1f77bcf86cd799439010"

    @pytest.mark.asyncio
    async def test_get_by_doctor_id(self):
        docs = [make_document_doc(), make_document_doc("507f1f77bcf86cd799439021")]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorDocumentRepository(collection)
        results = await repo.get_by_doctor_id("507f1f77bcf86cd799439010")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_pending_documents(self):
        docs = [make_document_doc()]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorDocumentRepository(collection)
        results = await repo.get_pending_documents()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_update_document(self):
        updated_doc = make_document_doc()
        updated_doc["document_url"] = "https://example.com/new_license.pdf"
        collection = make_mock_collection(find_one_return=updated_doc)

        repo = DoctorDocumentRepository(collection)
        update = DoctorDocumentUpdate(document_url="https://example.com/new_license.pdf")
        result = await repo.update("507f1f77bcf86cd799439020", update)

        assert result is not None
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document(self):
        collection = make_mock_collection()
        repo = DoctorDocumentRepository(collection)
        result = await repo.delete("507f1f77bcf86cd799439020")
        assert result is True

    @pytest.mark.asyncio
    async def test_approve_document(self):
        now = utc_now()
        approved_doc = make_document_doc(status="approved")
        approved_doc["verified_at"] = now
        approved_doc["verified_by"] = "admin123"
        collection = make_mock_collection(find_one_return=approved_doc)

        repo = DoctorDocumentRepository(collection)
        result = await repo.approve_document("507f1f77bcf86cd799439020", "admin123")

        assert result is not None
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_document(self):
        now = utc_now()
        rejected_doc = make_document_doc(status="rejected")
        rejected_doc["verified_at"] = now
        rejected_doc["verified_by"] = "admin123"
        collection = make_mock_collection(find_one_return=rejected_doc)

        repo = DoctorDocumentRepository(collection)
        result = await repo.reject_document("507f1f77bcf86cd799439020", "admin123")

        assert result is not None
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_documents(self):
        docs = [make_document_doc()]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorDocumentRepository(collection)
        results = await repo.list_documents()
        assert len(results) == 1


# ===========================================================================
# DoctorAvailabilityRepository tests
# ===========================================================================

class TestDoctorAvailabilityRepository:

    @pytest.mark.asyncio
    async def test_create_availability(self):
        avail_doc = make_availability_doc()
        collection = make_mock_collection(find_one_return=avail_doc)
        collection.insert_one.return_value.inserted_id = ObjectId("507f1f77bcf86cd799439030")

        repo = DoctorAvailabilityRepository(collection)
        avail_create = DoctorAvailabilityCreate(
            doctor_id="507f1f77bcf86cd799439010",
            date="2026-06-22",
            day_of_week=DayOfWeek.MONDAY,
            start_time="09:00",
            end_time="17:00",
            slot_duration=30,
            active=True,
        )
        result = await repo.create(avail_create)

        assert isinstance(result, DoctorAvailabilityInDB)
        assert result.day_of_week == DayOfWeek.MONDAY

    @pytest.mark.asyncio
    async def test_get_availability(self):
        avail_doc = make_availability_doc()
        collection = make_mock_collection(find_one_return=avail_doc)

        repo = DoctorAvailabilityRepository(collection)
        result = await repo.get("507f1f77bcf86cd799439030")

        assert result is not None
        assert result.id == "507f1f77bcf86cd799439030"

    @pytest.mark.asyncio
    async def test_get_by_doctor_id(self):
        docs = [make_availability_doc(), make_availability_doc("507f1f77bcf86cd799439031")]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorAvailabilityRepository(collection)
        results = await repo.get_by_doctor_id("507f1f77bcf86cd799439010")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_active_by_doctor_id(self):
        docs = [make_availability_doc()]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorAvailabilityRepository(collection)
        results = await repo.get_active_by_doctor_id("507f1f77bcf86cd799439010")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_doctor_and_day(self):
        docs = [make_availability_doc()]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorAvailabilityRepository(collection)
        results = await repo.get_by_doctor_and_day("507f1f77bcf86cd799439010", DayOfWeek.MONDAY)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_update_availability(self):
        updated_doc = make_availability_doc()
        updated_doc["slot_duration"] = 60
        collection = make_mock_collection(find_one_return=updated_doc)

        repo = DoctorAvailabilityRepository(collection)
        update = DoctorAvailabilityUpdate(slot_duration=60)
        result = await repo.update("507f1f77bcf86cd799439030", update)

        assert result is not None
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_availability(self):
        collection = make_mock_collection()
        repo = DoctorAvailabilityRepository(collection)
        result = await repo.delete("507f1f77bcf86cd799439030")
        assert result is True

    @pytest.mark.asyncio
    async def test_set_active(self):
        deactivated_doc = make_availability_doc(active=False)
        collection = make_mock_collection(find_one_return=deactivated_doc)

        repo = DoctorAvailabilityRepository(collection)
        result = await repo.set_active("507f1f77bcf86cd799439030", False)

        assert result is not None
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_all_for_doctor(self):
        collection = make_mock_collection()
        collection.update_many.return_value.modified_count = 3

        repo = DoctorAvailabilityRepository(collection)
        count = await repo.deactivate_all_for_doctor("507f1f77bcf86cd799439010")
        assert count == 3

    @pytest.mark.asyncio
    async def test_list_availability(self):
        docs = [make_availability_doc()]
        collection = make_mock_collection(find_return=docs)

        repo = DoctorAvailabilityRepository(collection)
        results = await repo.list_availability()
        assert len(results) == 1
