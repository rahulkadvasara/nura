"""
Nura - Appointment Repositories Tests
Unit tests for AppointmentRepository, ConsultationRepository, and PrescriptionRepository
using mocked MongoDB collections.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from app.models.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentInDB,
    AppointmentStatus,
    PaymentStatus,
    ConsultationCreate,
    ConsultationUpdate,
    ConsultationInDB,
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionInDB,
    Medication,
)
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.prescription_repository import PrescriptionRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_appointment_doc(
    appointment_id: str = "507f1f77bcf86cd799439050",
    patient_id: str = "507f1f77bcf86cd799439001",
    doctor_id: str = "507f1f77bcf86cd799439010",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(appointment_id),
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "slot_date": "2026-06-25",
        "slot_time": "10:00",
        "duration_minutes": 30,
        "consultation_fee": 500.0,
        "status": "pending",
        "payment_status": "pending",
        "notes": "Regular checkup",
        "created_at": now,
        "updated_at": now,
    }


def make_consultation_doc(
    consultation_id: str = "507f1f77bcf86cd799439060",
    appointment_id: str = "507f1f77bcf86cd799439050",
    patient_id: str = "507f1f77bcf86cd799439001",
    doctor_id: str = "507f1f77bcf86cd799439010",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(consultation_id),
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "consultation_notes": "Doing fine.",
        "diagnosis": "Common Cold",
        "recommendations": "Rest",
        "follow_up_required": False,
        "follow_up_date": None,
        "created_at": now,
        "updated_at": now,
    }


def make_prescription_doc(
    prescription_id: str = "507f1f77bcf86cd799439070",
    consultation_id: str = "507f1f77bcf86cd799439060",
    patient_id: str = "507f1f77bcf86cd799439001",
    doctor_id: str = "507f1f77bcf86cd799439010",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(prescription_id),
        "consultation_id": consultation_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "medications": [
            {
                "drug_name": "Paracetamol",
                "dosage": "500mg",
                "frequency": "once daily",
                "duration": "3 days",
            }
        ],
        "dosage_instructions": "Take with food",
        "notes": None,
        "created_at": now,
        "updated_at": now,
    }


def make_mock_collection(find_one_return=None, find_return=None, update_result=None):
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)

    insert_result = MagicMock()
    insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439050")
    collection.insert_one = AsyncMock(return_value=insert_result)

    upd_result = MagicMock()
    upd_result.modified_count = 1 if update_result is None else update_result
    collection.update_one = AsyncMock(return_value=upd_result)

    del_result = MagicMock()
    del_result.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=del_result)

    cursor = MagicMock()
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=find_return or [])
    collection.find = MagicMock(return_value=cursor)

    return collection


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------

class TestAppointmentRepository:
    @pytest.mark.asyncio
    async def test_create_appointment(self):
        doc = make_appointment_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = AppointmentRepository(collection)

        appointment_create = AppointmentCreate(
            patient_id="507f1f77bcf86cd799439001",
            doctor_id="507f1f77bcf86cd799439010",
            slot_date="2026-06-25",
            slot_time="10:00",
            consultation_fee=500.0,
        )
        result = await repo.create(appointment_create)
        assert isinstance(result, AppointmentInDB)
        assert result.patient_id == "507f1f77bcf86cd799439001"
        assert result.duration_minutes == 30

    @pytest.mark.asyncio
    async def test_get_appointment(self):
        doc = make_appointment_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = AppointmentRepository(collection)

        result = await repo.get_by_id("507f1f77bcf86cd799439050")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439050"

    @pytest.mark.asyncio
    async def test_get_by_patient_id(self):
        docs = [make_appointment_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = AppointmentRepository(collection)

        results = await repo.get_by_patient_id("507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert results[0].patient_id == "507f1f77bcf86cd799439001"

    @pytest.mark.asyncio
    async def test_get_by_doctor_id(self):
        docs = [make_appointment_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = AppointmentRepository(collection)

        results = await repo.get_by_doctor_id("507f1f77bcf86cd799439010")
        assert len(results) == 1
        assert results[0].doctor_id == "507f1f77bcf86cd799439010"

    @pytest.mark.asyncio
    async def test_update_appointment(self):
        updated_doc = make_appointment_doc()
        updated_doc["status"] = "approved"
        collection = make_mock_collection(find_one_return=updated_doc)
        repo = AppointmentRepository(collection)

        update = AppointmentUpdate(status=AppointmentStatus.APPROVED)
        result = await repo.update("507f1f77bcf86cd799439050", update)
        assert result is not None
        assert result.status == AppointmentStatus.APPROVED

    @pytest.mark.asyncio
    async def test_delete_appointment(self):
        collection = make_mock_collection()
        repo = AppointmentRepository(collection)
        result = await repo.delete("507f1f77bcf86cd799439050")
        assert result is True

    @pytest.mark.asyncio
    async def test_list_appointments(self):
        docs = [make_appointment_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = AppointmentRepository(collection)

        results = await repo.list()
        assert len(results) == 1


class TestConsultationRepository:
    @pytest.mark.asyncio
    async def test_create_consultation(self):
        doc = make_consultation_doc()
        collection = make_mock_collection(find_one_return=doc)
        collection.insert_one.return_value.inserted_id = ObjectId("507f1f77bcf86cd799439060")
        repo = ConsultationRepository(collection)

        consultation_create = ConsultationCreate(
            appointment_id="507f1f77bcf86cd799439050",
            patient_id="507f1f77bcf86cd799439001",
            doctor_id="507f1f77bcf86cd799439010",
            consultation_notes="Doing fine.",
            diagnosis="Common Cold",
            recommendations="Rest",
        )
        result = await repo.create(consultation_create)
        assert isinstance(result, ConsultationInDB)
        assert result.id == "507f1f77bcf86cd799439060"

    @pytest.mark.asyncio
    async def test_get_by_appointment_id(self):
        doc = make_consultation_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = ConsultationRepository(collection)

        result = await repo.get_by_appointment_id("507f1f77bcf86cd799439050")
        assert result is not None
        assert result.appointment_id == "507f1f77bcf86cd799439050"


class TestPrescriptionRepository:
    @pytest.mark.asyncio
    async def test_create_prescription(self):
        doc = make_prescription_doc()
        collection = make_mock_collection(find_one_return=doc)
        collection.insert_one.return_value.inserted_id = ObjectId("507f1f77bcf86cd799439070")
        repo = PrescriptionRepository(collection)

        meds = [
            Medication(
                drug_name="Paracetamol",
                dosage="500mg",
                frequency="once daily",
                duration="3 days",
            )
        ]
        prescription_create = PrescriptionCreate(
            consultation_id="507f1f77bcf86cd799439060",
            patient_id="507f1f77bcf86cd799439001",
            doctor_id="507f1f77bcf86cd799439010",
            medications=meds,
        )
        result = await repo.create(prescription_create)
        assert isinstance(result, PrescriptionInDB)
        assert result.id == "507f1f77bcf86cd799439070"

    @pytest.mark.asyncio
    async def test_get_by_consultation_id(self):
        doc = make_prescription_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = PrescriptionRepository(collection)

        result = await repo.get_by_consultation_id("507f1f77bcf86cd799439060")
        assert result is not None
        assert result.consultation_id == "507f1f77bcf86cd799439060"
