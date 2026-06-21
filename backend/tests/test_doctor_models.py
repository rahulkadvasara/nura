"""
Nura - Doctor Models Tests
Tests for doctor_profiles, doctor_documents, and doctor_availability Pydantic models
"""

import pytest
from datetime import datetime, timezone

from app.models.doctor import (
    DoctorProfileStatus,
    DocumentType,
    DocumentVerificationStatus,
    DayOfWeek,
    DoctorProfileCreate,
    DoctorProfileUpdate,
    DoctorProfileInDB,
    DoctorDocumentCreate,
    DoctorDocumentUpdate,
    DoctorDocumentInDB,
    DoctorAvailabilityCreate,
    DoctorAvailabilityUpdate,
    DoctorAvailabilityInDB,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_profile_create():
    return DoctorProfileCreate(
        user_id="507f1f77bcf86cd799439001",
        specialization="Cardiology",
        qualifications=["MBBS", "MD"],
        experience_years=10,
        consultation_fee=500.0,
        bio="Expert cardiologist with 10 years of experience.",
        languages=["English", "Hindi"],
        hospital="City Heart Hospital",
        license_number="MH-12345",
    )


@pytest.fixture
def sample_profile_in_db():
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
def sample_document_create():
    return DoctorDocumentCreate(
        doctor_id="507f1f77bcf86cd799439010",
        document_type=DocumentType.LICENSE,
        document_url="https://example.com/docs/license.pdf",
        verification_status=DocumentVerificationStatus.PENDING,
    )


@pytest.fixture
def sample_document_in_db():
    now = utc_now()
    return DoctorDocumentInDB(
        id="507f1f77bcf86cd799439020",
        doctor_id="507f1f77bcf86cd799439010",
        document_type=DocumentType.LICENSE,
        document_url="https://example.com/docs/license.pdf",
        verification_status=DocumentVerificationStatus.PENDING,
        uploaded_at=now,
    )


@pytest.fixture
def sample_availability_create():
    return DoctorAvailabilityCreate(
        doctor_id="507f1f77bcf86cd799439010",
        day_of_week=DayOfWeek.MONDAY,
        start_time="09:00",
        end_time="17:00",
        slot_duration=30,
        active=True,
    )


@pytest.fixture
def sample_availability_in_db():
    return DoctorAvailabilityInDB(
        id="507f1f77bcf86cd799439030",
        doctor_id="507f1f77bcf86cd799439010",
        day_of_week=DayOfWeek.MONDAY,
        start_time="09:00",
        end_time="17:00",
        slot_duration=30,
        active=True,
    )


# ---------------------------------------------------------------------------
# Enumeration tests
# ---------------------------------------------------------------------------

class TestEnumerations:
    def test_profile_status_values(self):
        assert DoctorProfileStatus.PENDING == "pending"
        assert DoctorProfileStatus.VERIFIED == "verified"
        assert DoctorProfileStatus.REJECTED == "rejected"

    def test_document_type_values(self):
        assert DocumentType.LICENSE == "license"
        assert DocumentType.DEGREE == "degree"
        assert DocumentType.CERTIFICATE == "certificate"
        assert DocumentType.ID_PROOF == "id_proof"
        assert DocumentType.OTHER == "other"

    def test_document_verification_status_values(self):
        assert DocumentVerificationStatus.PENDING == "pending"
        assert DocumentVerificationStatus.APPROVED == "approved"
        assert DocumentVerificationStatus.REJECTED == "rejected"

    def test_day_of_week_values(self):
        assert DayOfWeek.MONDAY == "monday"
        assert DayOfWeek.SUNDAY == "sunday"
        assert len(list(DayOfWeek)) == 7


# ---------------------------------------------------------------------------
# DoctorProfile model tests
# ---------------------------------------------------------------------------

class TestDoctorProfileModel:
    def test_create_profile(self, sample_profile_create):
        profile = sample_profile_create
        assert profile.user_id == "507f1f77bcf86cd799439001"
        assert profile.specialization == "Cardiology"
        assert profile.experience_years == 10
        assert profile.consultation_fee == 500.0
        assert profile.profile_status == DoctorProfileStatus.PENDING
        assert profile.average_rating == 0.0
        assert profile.total_reviews == 0

    def test_profile_default_values(self):
        profile = DoctorProfileCreate(
            user_id="507f1f77bcf86cd799439001",
            specialization="Neurology",
            experience_years=5,
            consultation_fee=700.0,
        )
        assert profile.qualifications == []
        assert profile.languages == []
        assert profile.bio is None
        assert profile.hospital is None
        assert profile.license_number is None
        assert profile.profile_status == DoctorProfileStatus.PENDING
        assert profile.average_rating == 0.0
        assert profile.total_reviews == 0

    def test_profile_update_partial(self):
        update = DoctorProfileUpdate(specialization="Neurology", experience_years=12)
        assert update.specialization == "Neurology"
        assert update.experience_years == 12
        assert update.consultation_fee is None  # not set

    def test_profile_update_empty(self):
        update = DoctorProfileUpdate()
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_profile_in_db_fields(self, sample_profile_in_db):
        profile = sample_profile_in_db
        assert profile.id == "507f1f77bcf86cd799439010"
        assert profile.profile_status == DoctorProfileStatus.PENDING
        assert isinstance(profile.created_at, datetime)
        assert isinstance(profile.updated_at, datetime)

    def test_profile_from_mongo(self):
        from bson import ObjectId
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439010"),
            "user_id": "507f1f77bcf86cd799439001",
            "specialization": "Cardiology",
            "qualifications": [],
            "experience_years": 5,
            "consultation_fee": 500.0,
            "bio": None,
            "languages": [],
            "hospital": None,
            "license_number": None,
            "profile_status": "pending",
            "average_rating": 0.0,
            "total_reviews": 0,
            "created_at": now,
            "updated_at": now,
        }
        profile = DoctorProfileInDB.from_mongo(raw)
        assert profile.id == "507f1f77bcf86cd799439010"
        assert profile.specialization == "Cardiology"

    def test_experience_years_constraints(self):
        with pytest.raises(Exception):
            DoctorProfileCreate(
                user_id="abc",
                specialization="X",
                experience_years=-1,
                consultation_fee=500.0,
            )
        with pytest.raises(Exception):
            DoctorProfileCreate(
                user_id="abc",
                specialization="X",
                experience_years=81,
                consultation_fee=500.0,
            )

    def test_consultation_fee_non_negative(self):
        with pytest.raises(Exception):
            DoctorProfileCreate(
                user_id="abc",
                specialization="X",
                experience_years=5,
                consultation_fee=-100.0,
            )


# ---------------------------------------------------------------------------
# DoctorDocument model tests
# ---------------------------------------------------------------------------

class TestDoctorDocumentModel:
    def test_create_document(self, sample_document_create):
        doc = sample_document_create
        assert doc.doctor_id == "507f1f77bcf86cd799439010"
        assert doc.document_type == DocumentType.LICENSE
        assert doc.verification_status == DocumentVerificationStatus.PENDING

    def test_document_update_partial(self):
        update = DoctorDocumentUpdate(verification_status=DocumentVerificationStatus.APPROVED)
        assert update.verification_status == DocumentVerificationStatus.APPROVED
        assert update.document_type is None
        assert update.document_url is None

    def test_document_update_empty(self):
        update = DoctorDocumentUpdate()
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_document_in_db_fields(self, sample_document_in_db):
        doc = sample_document_in_db
        assert doc.id == "507f1f77bcf86cd799439020"
        assert doc.verification_status == DocumentVerificationStatus.PENDING
        assert doc.verified_at is None
        assert doc.verified_by is None

    def test_document_from_mongo(self):
        from bson import ObjectId
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439020"),
            "doctor_id": ObjectId("507f1f77bcf86cd799439010"),
            "document_type": "license",
            "document_url": "https://example.com/license.pdf",
            "verification_status": "pending",
            "uploaded_at": now,
            "verified_at": None,
            "verified_by": None,
        }
        doc = DoctorDocumentInDB.from_mongo(raw)
        assert doc.id == "507f1f77bcf86cd799439020"
        # ObjectId fields should be stringified
        assert doc.doctor_id == "507f1f77bcf86cd799439010"


# ---------------------------------------------------------------------------
# DoctorAvailability model tests
# ---------------------------------------------------------------------------

class TestDoctorAvailabilityModel:
    def test_create_availability(self, sample_availability_create):
        avail = sample_availability_create
        assert avail.doctor_id == "507f1f77bcf86cd799439010"
        assert avail.day_of_week == DayOfWeek.MONDAY
        assert avail.start_time == "09:00"
        assert avail.end_time == "17:00"
        assert avail.slot_duration == 30
        assert avail.active is True

    def test_availability_default_values(self):
        avail = DoctorAvailabilityCreate(
            doctor_id="abc",
            day_of_week=DayOfWeek.FRIDAY,
            start_time="10:00",
            end_time="12:00",
        )
        assert avail.slot_duration == 30
        assert avail.active is True

    def test_availability_update_partial(self):
        update = DoctorAvailabilityUpdate(active=False)
        assert update.active is False
        assert update.start_time is None

    def test_availability_update_empty(self):
        update = DoctorAvailabilityUpdate()
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_availability_in_db_fields(self, sample_availability_in_db):
        avail = sample_availability_in_db
        assert avail.id == "507f1f77bcf86cd799439030"
        assert avail.active is True

    def test_availability_from_mongo(self):
        from bson import ObjectId
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439030"),
            "doctor_id": ObjectId("507f1f77bcf86cd799439010"),
            "day_of_week": "monday",
            "start_time": "09:00",
            "end_time": "17:00",
            "slot_duration": 30,
            "active": True,
        }
        avail = DoctorAvailabilityInDB.from_mongo(raw)
        assert avail.id == "507f1f77bcf86cd799439030"
        assert avail.doctor_id == "507f1f77bcf86cd799439010"

    def test_time_pattern_validation(self):
        with pytest.raises(Exception):
            DoctorAvailabilityCreate(
                doctor_id="abc",
                day_of_week=DayOfWeek.MONDAY,
                start_time="9:00",   # missing leading zero
                end_time="17:00",
            )

    def test_slot_duration_constraints(self):
        with pytest.raises(Exception):
            DoctorAvailabilityCreate(
                doctor_id="abc",
                day_of_week=DayOfWeek.MONDAY,
                start_time="09:00",
                end_time="17:00",
                slot_duration=4,  # below minimum of 5
            )
        with pytest.raises(Exception):
            DoctorAvailabilityCreate(
                doctor_id="abc",
                day_of_week=DayOfWeek.MONDAY,
                start_time="09:00",
                end_time="17:00",
                slot_duration=241,  # above maximum of 240
            )
