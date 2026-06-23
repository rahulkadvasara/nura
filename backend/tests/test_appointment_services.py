"""
Nura - Appointment, Consultation, and Prescription Services Tests
Unit tests for AppointmentService, ConsultationService, and PrescriptionService using mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.appointment import (
    AppointmentInDB,
    AppointmentStatus,
    PaymentStatus,
    ConsultationInDB,
    PrescriptionInDB,
    Medication,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.schemas.appointment import (
    AppointmentCreateSchema,
    AppointmentUpdateSchema,
    ConsultationCreateSchema,
    ConsultationUpdateSchema,
    PrescriptionCreateSchema,
    PrescriptionUpdateSchema,
    MedicationSchema,
)
from app.services.appointment_service import AppointmentService
from app.services.consultation_service import ConsultationService
from app.services.prescription_service import PrescriptionService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user():
    return UserInDB(
        id="507f1f77bcf86cd799439001",
        role=UserRole.PATIENT,
        email="patient@example.com",
        password_hash="hashed_pw",
        full_name="Patient Name",
        phone="1234567890",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_doctor_profile():
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439010",
        user_id="507f1f77bcf86cd799439002",
        specialization="Cardiology",
        qualifications=["MBBS"],
        experience_years=10,
        consultation_fee=500.0,
        bio="Cardiologist",
        languages=["English"],
        profile_status=DoctorProfileStatus.VERIFIED,
        average_rating=4.8,
        total_reviews=12,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_appointment():
    return AppointmentInDB(
        id="507f1f77bcf86cd799439050",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439010",
        slot_date="2026-06-25",
        slot_time="10:00",
        duration_minutes=30,
        consultation_fee=500.0,
        status=AppointmentStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        notes="Regular checkup",
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_consultation():
    return ConsultationInDB(
        id="507f1f77bcf86cd799439060",
        appointment_id="507f1f77bcf86cd799439050",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439010",
        consultation_notes="Patient is doing fine.",
        diagnosis="Common Cold",
        recommendations="Rest",
        follow_up_required=False,
        follow_up_date=None,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_prescription():
    return PrescriptionInDB(
        id="507f1f77bcf86cd799439070",
        consultation_id="507f1f77bcf86cd799439060",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439010",
        medications=[
            Medication(
                drug_name="Paracetamol",
                dosage="500mg",
                frequency="once daily",
                duration="3 days",
            )
        ],
        dosage_instructions="Take with food",
        notes="Avoid cold drinks",
        created_at=utc_now(),
        updated_at=utc_now(),
    )


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestAppointmentService:
    @pytest.mark.asyncio
    async def test_create_appointment_success(self, sample_user, sample_doctor_profile, sample_appointment):
        app_repo = AsyncMock()
        app_repo.collection = MagicMock()
        app_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439050"))
        )
        app_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439050"),
            "patient_id": sample_user.id,
            "doctor_id": sample_doctor_profile.id,
            "slot_date": "2026-06-25",
            "slot_time": "10:00",
            "duration_minutes": 30,
            "consultation_fee": 500.0,
            "status": "pending",
            "payment_status": "pending",
            "notes": "Regular checkup",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })
        app_repo.get_many = AsyncMock(return_value=[])

        doc_repo = AsyncMock()
        doc_repo.get = AsyncMock(return_value=sample_doctor_profile)

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_user)

        doc_avail_repo = AsyncMock()
        slot = MagicMock()
        slot.id = "507f1f77bcf86cd799439020"
        slot.doctor_id = sample_doctor_profile.id
        slot.date = "2026-06-25"
        slot.start_time = "10:00"
        slot.end_time = "10:30"
        slot.slot_duration = 30
        slot.is_available = True
        slot.active = True
        doc_avail_repo.get = AsyncMock(return_value=slot)

        service = AppointmentService(app_repo, doc_repo, user_repo, doc_avail_repo)
        schema = AppointmentCreateSchema(
            doctor_id=sample_doctor_profile.id,
            availability_id="507f1f77bcf86cd799439020",
            reason="Regular checkup",
            slot_date="2026-06-25",
            slot_time="10:00",
            consultation_fee=500.0,
            notes="Regular checkup",
        )

        result = await service.create_appointment(sample_user.id, schema)
        assert isinstance(result, AppointmentInDB)
        assert result.id == "507f1f77bcf86cd799439050"
        user_repo.get.assert_called_once_with(sample_user.id)
        doc_repo.get.assert_called_once_with(sample_doctor_profile.id)
        doc_avail_repo.get.assert_called_once_with("507f1f77bcf86cd799439020")

    @pytest.mark.asyncio
    async def test_create_appointment_patient_not_found(self, sample_doctor_profile):
        app_repo = AsyncMock()
        doc_repo = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None)

        service = AppointmentService(app_repo, doc_repo, user_repo)
        schema = AppointmentCreateSchema(
            doctor_id=sample_doctor_profile.id,
            availability_id="507f1f77bcf86cd799439020",
            reason="Patient not found test",
            slot_date="2026-06-25",
            slot_time="10:00",
            consultation_fee=500.0,
        )

        with pytest.raises(ValueError, match="Patient.*does not exist"):
            await service.create_appointment("invalid_patient", schema)

    @pytest.mark.asyncio
    async def test_create_appointment_doctor_not_found(self, sample_user):
        app_repo = AsyncMock()
        doc_repo = AsyncMock()
        doc_repo.get = AsyncMock(return_value=None)
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_user)

        service = AppointmentService(app_repo, doc_repo, user_repo)
        schema = AppointmentCreateSchema(
            doctor_id="invalid_doctor",
            availability_id="507f1f77bcf86cd799439020",
            reason="Doctor not found test",
            slot_date="2026-06-25",
            slot_time="10:00",
            consultation_fee=500.0,
        )

        with pytest.raises(ValueError, match="Doctor.*does not exist"):
            await service.create_appointment(sample_user.id, schema)



class TestConsultationService:
    @pytest.mark.asyncio
    async def test_create_consultation_success(self, sample_appointment, sample_consultation):
        cons_repo = AsyncMock()
        cons_repo.collection = MagicMock()
        cons_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439060"))
        )
        cons_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439060"),
            "appointment_id": sample_appointment.id,
            "patient_id": sample_appointment.patient_id,
            "doctor_id": sample_appointment.doctor_id,
            "consultation_notes": "Doing fine.",
            "diagnosis": "Common Cold",
            "recommendations": "Rest",
            "follow_up_required": False,
            "follow_up_date": None,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })

        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)

        service = ConsultationService(cons_repo, app_repo)
        schema = ConsultationCreateSchema(
            appointment_id=sample_appointment.id,
            patient_id=sample_appointment.patient_id,
            doctor_id=sample_appointment.doctor_id,
            consultation_notes="Doing fine.",
            diagnosis="Common Cold",
            recommendations="Rest",
        )

        result = await service.create_consultation(schema)
        assert isinstance(result, ConsultationInDB)
        assert result.id == "507f1f77bcf86cd799439060"
        app_repo.get.assert_called_once_with(sample_appointment.id)

    @pytest.mark.asyncio
    async def test_create_consultation_appointment_not_found(self):
        cons_repo = AsyncMock()
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=None)

        service = ConsultationService(cons_repo, app_repo)
        schema = ConsultationCreateSchema(
            appointment_id="invalid_app",
            patient_id="patient_1",
            doctor_id="doctor_1",
            consultation_notes="Some notes",
            diagnosis="None",
            recommendations="None",
        )

        with pytest.raises(ValueError, match="Appointment.*does not exist"):
            await service.create_consultation(schema)


class TestPrescriptionService:
    @pytest.mark.asyncio
    async def test_create_prescription_success(self, sample_consultation, sample_prescription):
        pres_repo = AsyncMock()
        pres_repo.collection = MagicMock()
        pres_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439070"))
        )
        pres_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439070"),
            "consultation_id": sample_consultation.id,
            "patient_id": sample_consultation.patient_id,
            "doctor_id": sample_consultation.doctor_id,
            "medications": [
                {
                    "drug_name": "Paracetamol",
                    "dosage": "500mg",
                    "frequency": "once daily",
                    "duration": "3 days",
                }
            ],
            "dosage_instructions": "Take with food",
            "notes": "Avoid cold drinks",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })

        cons_repo = AsyncMock()
        cons_repo.get = AsyncMock(return_value=sample_consultation)

        service = PrescriptionService(pres_repo, cons_repo)
        meds_schema = [
            MedicationSchema(
                drug_name="Paracetamol",
                dosage="500mg",
                frequency="once daily",
                duration="3 days",
            )
        ]
        schema = PrescriptionCreateSchema(
            consultation_id=sample_consultation.id,
            patient_id=sample_consultation.patient_id,
            doctor_id=sample_consultation.doctor_id,
            medications=meds_schema,
            dosage_instructions="Take with food",
            notes="Avoid cold drinks",
        )

        result = await service.create_prescription(schema)
        assert isinstance(result, PrescriptionInDB)
        assert result.id == "507f1f77bcf86cd799439070"
        cons_repo.get.assert_called_once_with(sample_consultation.id)

    @pytest.mark.asyncio
    async def test_create_prescription_consultation_not_found(self):
        pres_repo = AsyncMock()
        cons_repo = AsyncMock()
        cons_repo.get = AsyncMock(return_value=None)

        service = PrescriptionService(pres_repo, cons_repo)
        meds_schema = [
            MedicationSchema(
                drug_name="Paracetamol",
                dosage="500mg",
                frequency="once daily",
                duration="3 days",
            )
        ]
        schema = PrescriptionCreateSchema(
            consultation_id="invalid_cons",
            patient_id="patient_1",
            doctor_id="doctor_1",
            medications=meds_schema,
        )

        with pytest.raises(ValueError, match="Consultation.*does not exist"):
            await service.create_prescription(schema)
