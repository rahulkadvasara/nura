"""
Nura - Doctor Services Tests
Unit tests for DoctorProfileService, DoctorDocumentService,
and DoctorAvailabilityService using mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from app.models.doctor import (
    DoctorProfileInDB,
    DoctorProfileStatus,
    DoctorDocumentInDB,
    DocumentVerificationStatus,
    DocumentType,
    DoctorAvailabilityInDB,
    DayOfWeek,
)
from app.schemas.doctor import (
    DoctorProfileCreateSchema,
    DoctorProfileUpdateSchema,
    DoctorDocumentCreateSchema,
    DoctorDocumentUpdateSchema,
    DoctorAvailabilityCreateSchema,
    DoctorAvailabilityUpdateSchema,
)
from app.services.doctor_service import (
    DoctorProfileService,
    DoctorDocumentService,
    DoctorAvailabilityService,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures – pre-built in-memory models
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_profile():
    now = utc_now()
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439010",
        user_id="507f1f77bcf86cd799439001",
        specialization="Cardiology",
        qualifications=["MBBS", "MD"],
        experience_years=10,
        consultation_fee=500.0,
        bio="Expert cardiologist.",
        languages=["English"],
        hospital="City Heart Hospital",
        license_number="MH-12345",
        profile_status=DoctorProfileStatus.PENDING,
        average_rating=0.0,
        total_reviews=0,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_document():
    now = utc_now()
    return DoctorDocumentInDB(
        id="507f1f77bcf86cd799439020",
        doctor_id="507f1f77bcf86cd799439010",
        document_type=DocumentType.LICENSE,
        document_url="https://example.com/license.pdf",
        verification_status=DocumentVerificationStatus.PENDING,
        uploaded_at=now,
    )


@pytest.fixture
def sample_availability():
    return DoctorAvailabilityInDB(
        id="507f1f77bcf86cd799439030",
        doctor_id="507f1f77bcf86cd799439010",
        date="2026-06-22",
        day_of_week=DayOfWeek.MONDAY,
        start_time="09:00",
        end_time="17:00",
        slot_duration=30,
        active=True,
    )


# ===========================================================================
# DoctorProfileService tests
# ===========================================================================

class TestDoctorProfileService:

    def _make_service(self, sample_profile):
        repo = AsyncMock()
        repo.exists_for_user = AsyncMock(return_value=False)
        repo.collection = MagicMock()
        # Simulate insert + find cycle
        repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439010"))
        )
        repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439010"),
            "user_id": "507f1f77bcf86cd799439001",
            "specialization": "Cardiology",
            "qualifications": ["MBBS"],
            "experience_years": 10,
            "consultation_fee": 500.0,
            "bio": "Expert cardiologist.",
            "languages": ["English"],
            "hospital": "City Heart Hospital",
            "license_number": "MH-12345",
            "profile_status": "pending",
            "average_rating": 0.0,
            "total_reviews": 0,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })
        repo.get = AsyncMock(return_value=sample_profile)
        repo.get_by_user_id = AsyncMock(return_value=sample_profile)
        repo.update = AsyncMock(return_value=sample_profile)
        repo.delete = AsyncMock(return_value=True)
        repo.get_verified_doctors = AsyncMock(return_value=[sample_profile])
        repo.get_by_status = AsyncMock(return_value=[sample_profile])
        repo.list_profiles = AsyncMock(return_value=[sample_profile])
        repo.update_status = AsyncMock(return_value=sample_profile)
        return DoctorProfileService(repo), repo

    @pytest.mark.asyncio
    async def test_create_profile(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        schema = DoctorProfileCreateSchema(
            specialization="Cardiology",
            qualifications=["MBBS"],
            experience_years=10,
            consultation_fee=500.0,
        )
        result = await service.create_profile("507f1f77bcf86cd799439001", schema)
        assert isinstance(result, DoctorProfileInDB)
        assert result.specialization == "Cardiology"

    @pytest.mark.asyncio
    async def test_create_profile_duplicate_raises(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        repo.exists_for_user = AsyncMock(return_value=True)

        schema = DoctorProfileCreateSchema(
            specialization="Cardiology",
            experience_years=10,
            consultation_fee=500.0,
        )
        with pytest.raises(ValueError, match="already exists"):
            await service.create_profile("507f1f77bcf86cd799439001", schema)

    @pytest.mark.asyncio
    async def test_get_profile_by_id(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        result = await service.get_profile_by_id("507f1f77bcf86cd799439010")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439010"

    @pytest.mark.asyncio
    async def test_get_profile_by_user_id(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        result = await service.get_profile_by_user_id("507f1f77bcf86cd799439001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_list_profiles(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        results = await service.list_profiles()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_list_verified_doctors(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        results = await service.list_verified_doctors()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_update_profile(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        schema = DoctorProfileUpdateSchema(specialization="Neurology", experience_years=12)
        result = await service.update_profile("507f1f77bcf86cd799439010", schema)
        assert result is not None
        repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_profile(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        result = await service.verify_profile("507f1f77bcf86cd799439010")
        assert result is not None
        repo.update_status.assert_called_once_with(
            "507f1f77bcf86cd799439010", DoctorProfileStatus.VERIFIED
        )

    @pytest.mark.asyncio
    async def test_reject_profile(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        result = await service.reject_profile("507f1f77bcf86cd799439010")
        assert result is not None
        repo.update_status.assert_called_once_with(
            "507f1f77bcf86cd799439010", DoctorProfileStatus.REJECTED, None
        )

    @pytest.mark.asyncio
    async def test_delete_profile(self, sample_profile):
        service, repo = self._make_service(sample_profile)
        result = await service.delete_profile("507f1f77bcf86cd799439010")
        assert result is True

    def test_to_response(self, sample_profile):
        service, _ = self._make_service(sample_profile)
        response = service.to_response(sample_profile)
        assert response.id == sample_profile.id
        assert response.specialization == sample_profile.specialization


# ===========================================================================
# DoctorDocumentService tests
# ===========================================================================

class TestDoctorDocumentService:

    def _make_service(self, sample_document):
        repo = AsyncMock()
        repo.collection = MagicMock()
        repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439020"))
        )
        now = utc_now()
        repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439020"),
            "doctor_id": "507f1f77bcf86cd799439010",
            "document_type": "license",
            "document_url": "https://example.com/license.pdf",
            "verification_status": "pending",
            "uploaded_at": now,
            "verified_at": None,
            "verified_by": None,
        })
        repo.get = AsyncMock(return_value=sample_document)
        repo.get_by_doctor_id = AsyncMock(return_value=[sample_document])
        repo.get_pending_documents = AsyncMock(return_value=[sample_document])
        repo.update = AsyncMock(return_value=sample_document)
        repo.delete = AsyncMock(return_value=True)
        repo.approve_document = AsyncMock(return_value=sample_document)
        repo.reject_document = AsyncMock(return_value=sample_document)
        repo.list_documents = AsyncMock(return_value=[sample_document])
        return DoctorDocumentService(repo), repo

    @pytest.mark.asyncio
    async def test_upload_document(self, sample_document):
        service, repo = self._make_service(sample_document)
        schema = DoctorDocumentCreateSchema(
            document_type=DocumentType.LICENSE,
            document_url="https://example.com/license.pdf",
        )
        result = await service.upload_document("507f1f77bcf86cd799439010", schema)
        assert isinstance(result, DoctorDocumentInDB)
        assert result.document_type == DocumentType.LICENSE

    @pytest.mark.asyncio
    async def test_get_document_by_id(self, sample_document):
        service, repo = self._make_service(sample_document)
        result = await service.get_document_by_id("507f1f77bcf86cd799439020")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_documents_by_doctor(self, sample_document):
        service, repo = self._make_service(sample_document)
        results = await service.get_documents_by_doctor("507f1f77bcf86cd799439010")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_list_pending_documents(self, sample_document):
        service, repo = self._make_service(sample_document)
        results = await service.list_pending_documents()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_update_document(self, sample_document):
        service, repo = self._make_service(sample_document)
        schema = DoctorDocumentUpdateSchema(document_url="https://example.com/new.pdf")
        result = await service.update_document("507f1f77bcf86cd799439020", schema)
        assert result is not None
        repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_document(self, sample_document):
        service, repo = self._make_service(sample_document)
        result = await service.approve_document("507f1f77bcf86cd799439020", "admin123")
        assert result is not None
        repo.approve_document.assert_called_once_with("507f1f77bcf86cd799439020", "admin123")

    @pytest.mark.asyncio
    async def test_reject_document(self, sample_document):
        service, repo = self._make_service(sample_document)
        result = await service.reject_document("507f1f77bcf86cd799439020", "admin123")
        assert result is not None
        repo.reject_document.assert_called_once_with("507f1f77bcf86cd799439020", "admin123")

    @pytest.mark.asyncio
    async def test_delete_document(self, sample_document):
        service, repo = self._make_service(sample_document)
        result = await service.delete_document("507f1f77bcf86cd799439020")
        assert result is True

    def test_to_response(self, sample_document):
        service, _ = self._make_service(sample_document)
        response = service.to_response(sample_document)
        assert response.id == sample_document.id
        assert response.document_type == DocumentType.LICENSE


# ===========================================================================
# DoctorAvailabilityService tests
# ===========================================================================

class TestDoctorAvailabilityService:

    def _make_service(self, sample_availability):
        from bson import ObjectId
        repo = AsyncMock()
        repo.create = AsyncMock(return_value=sample_availability)
        repo.get = AsyncMock(return_value=sample_availability)
        repo.get_by_doctor_id = AsyncMock(return_value=[sample_availability])
        repo.get_active_by_doctor_id = AsyncMock(return_value=[sample_availability])
        repo.get_by_doctor_and_day = AsyncMock(return_value=[sample_availability])
        repo.update = AsyncMock(return_value=sample_availability)
        repo.delete = AsyncMock(return_value=True)
        repo.set_active = AsyncMock(return_value=sample_availability)
        repo.list_availability = AsyncMock(return_value=[sample_availability])
        
        # Configure MongoDB collection mocks for create_availability
        repo.collection = AsyncMock()
        insert_result = MagicMock()
        insert_result.inserted_id = ObjectId(sample_availability.id)
        repo.collection.insert_one = AsyncMock(return_value=insert_result)
        
        avail_dict = sample_availability.model_dump()
        avail_dict["_id"] = ObjectId(avail_dict.pop("id"))
        repo.collection.find_one = AsyncMock(return_value=avail_dict)
        
        appt_repo = AsyncMock()
        appt_repo.exists = AsyncMock(return_value=False)
        
        return DoctorAvailabilityService(repo, appt_repo), repo

    @pytest.mark.asyncio
    async def test_create_availability(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        schema = DoctorAvailabilityCreateSchema(
            date="2026-06-22",
            day_of_week=DayOfWeek.MONDAY,
            start_time="09:00",
            end_time="17:00",
        )
        result = await service.create_availability("507f1f77bcf86cd799439010", schema)
        assert isinstance(result, DoctorAvailabilityInDB)
        assert result.day_of_week == DayOfWeek.MONDAY
        repo.collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_availability_invalid_time_range(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        schema = DoctorAvailabilityCreateSchema(
            date="2026-06-22",
            day_of_week=DayOfWeek.MONDAY,
            start_time="17:00",
            end_time="09:00",  # before start
        )
        with pytest.raises(ValueError, match="end_time"):
            await service.create_availability("507f1f77bcf86cd799439010", schema)

    @pytest.mark.asyncio
    async def test_create_availability_same_time_range(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        schema = DoctorAvailabilityCreateSchema(
            date="2026-06-22",
            day_of_week=DayOfWeek.MONDAY,
            start_time="09:00",
            end_time="09:00",  # same as start
        )
        with pytest.raises(ValueError, match="end_time"):
            await service.create_availability("507f1f77bcf86cd799439010", schema)

    @pytest.mark.asyncio
    async def test_get_availability_by_id(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        result = await service.get_availability_by_id("507f1f77bcf86cd799439030")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_availability_by_doctor(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        results = await service.get_availability_by_doctor("507f1f77bcf86cd799439010")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_active_availability(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        results = await service.get_active_availability("507f1f77bcf86cd799439010")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_availability_by_day(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        results = await service.get_availability_by_day("507f1f77bcf86cd799439010", DayOfWeek.MONDAY)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_update_availability(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        schema = DoctorAvailabilityUpdateSchema(slot_duration=60)
        result = await service.update_availability("507f1f77bcf86cd799439030", schema)
        assert result is not None
        repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_availability_invalid_time_range(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        # Update only end_time to be before existing start_time (09:00)
        schema = DoctorAvailabilityUpdateSchema(end_time="08:00")
        with pytest.raises(ValueError, match="end_time"):
            await service.update_availability("507f1f77bcf86cd799439030", schema)

    @pytest.mark.asyncio
    async def test_deactivate_availability(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        result = await service.deactivate_availability("507f1f77bcf86cd799439030")
        assert result is not None
        repo.set_active.assert_called_once_with("507f1f77bcf86cd799439030", False)

    @pytest.mark.asyncio
    async def test_activate_availability(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        result = await service.activate_availability("507f1f77bcf86cd799439030")
        assert result is not None
        repo.set_active.assert_called_once_with("507f1f77bcf86cd799439030", True)

    @pytest.mark.asyncio
    async def test_delete_availability(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        result = await service.delete_availability("507f1f77bcf86cd799439030")
        assert result is True

    @pytest.mark.asyncio
    async def test_list_availability(self, sample_availability):
        service, repo = self._make_service(sample_availability)
        results = await service.list_availability()
        assert len(results) == 1

    def test_to_response(self, sample_availability):
        service, _ = self._make_service(sample_availability)
        response = service.to_response(sample_availability)
        assert response.id == sample_availability.id
        assert response.day_of_week == DayOfWeek.MONDAY

    def test_validate_time_range_valid(self):
        # Should not raise
        DoctorAvailabilityService._validate_time_range("09:00", "17:00")
        DoctorAvailabilityService._validate_time_range("00:00", "23:59")

    def test_validate_time_range_invalid(self):
        with pytest.raises(ValueError):
            DoctorAvailabilityService._validate_time_range("17:00", "09:00")

    def test_validate_time_range_equal(self):
        with pytest.raises(ValueError):
            DoctorAvailabilityService._validate_time_range("09:00", "09:00")
