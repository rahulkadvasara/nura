"""
Nura - Appointment Models Tests
Tests for appointments, consultations, and prescriptions Pydantic models
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from app.models.appointment import (
    AppointmentStatus,
    PaymentStatus,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentInDB,
    ConsultationCreate,
    ConsultationUpdate,
    ConsultationInDB,
    Medication,
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionInDB,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TestAppointmentEnums:
    def test_appointment_status_values(self):
        assert AppointmentStatus.PENDING == "pending"
        assert AppointmentStatus.APPROVED == "approved"
        assert AppointmentStatus.REJECTED == "rejected"
        assert AppointmentStatus.CANCELLED == "cancelled"
        assert AppointmentStatus.COMPLETED == "completed"

    def test_payment_status_values(self):
        assert PaymentStatus.PENDING == "pending"
        assert PaymentStatus.HELD == "held"
        assert PaymentStatus.APPROVED == "approved"
        assert PaymentStatus.COMPLETED == "completed"
        assert PaymentStatus.REFUNDED == "refunded"
        assert PaymentStatus.FAILED == "failed"


class TestAppointmentModel:
    def test_create_appointment(self):
        appointment = AppointmentCreate(
            patient_id="507f1f77bcf86cd799439001",
            doctor_id="507f1f77bcf86cd799439010",
            slot_date="2026-06-25",
            slot_time="10:00",
            duration_minutes=30,
            consultation_fee=500.0,
            notes="Regular checkup"
        )
        assert appointment.patient_id == "507f1f77bcf86cd799439001"
        assert appointment.doctor_id == "507f1f77bcf86cd799439010"
        assert appointment.slot_date == "2026-06-25"
        assert appointment.slot_time == "10:00"
        assert appointment.status == AppointmentStatus.PENDING
        assert appointment.payment_status == PaymentStatus.PENDING
        assert appointment.notes == "Regular checkup"

    def test_appointment_default_values(self):
        appointment = AppointmentCreate(
            patient_id="patient_1",
            doctor_id="doctor_1",
            slot_date="2026-06-25",
            slot_time="10:00",
            consultation_fee=350.0,
        )
        assert appointment.duration_minutes == 30
        assert appointment.status == AppointmentStatus.PENDING
        assert appointment.payment_status == PaymentStatus.PENDING
        assert appointment.notes is None

    def test_appointment_update_partial(self):
        update = AppointmentUpdate(status=AppointmentStatus.APPROVED, notes="Updated notes")
        assert update.status == AppointmentStatus.APPROVED
        assert update.notes == "Updated notes"
        assert update.slot_date is None

    def test_appointment_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439050"),
            "patient_id": ObjectId("507f1f77bcf86cd799439001"),
            "doctor_id": ObjectId("507f1f77bcf86cd799439010"),
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
        appointment = AppointmentInDB.from_mongo(raw)
        assert appointment.id == "507f1f77bcf86cd799439050"
        assert appointment.patient_id == "507f1f77bcf86cd799439001"
        assert appointment.doctor_id == "507f1f77bcf86cd799439010"
        assert appointment.created_at == now


class TestConsultationModel:
    def test_create_consultation(self):
        consultation = ConsultationCreate(
            appointment_id="507f1f77bcf86cd799439050",
            patient_id="507f1f77bcf86cd799439001",
            doctor_id="507f1f77bcf86cd799439010",
            consultation_notes="Patient is doing fine.",
            diagnosis="Common Cold",
            recommendations="Rest for 2 days",
            follow_up_required=True,
            follow_up_date=utc_now()
        )
        assert consultation.appointment_id == "507f1f77bcf86cd799439050"
        assert consultation.diagnosis == "Common Cold"
        assert consultation.follow_up_required is True

    def test_consultation_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439060"),
            "appointment_id": ObjectId("507f1f77bcf86cd799439050"),
            "patient_id": ObjectId("507f1f77bcf86cd799439001"),
            "doctor_id": ObjectId("507f1f77bcf86cd799439010"),
            "consultation_notes": "Patient is doing fine.",
            "diagnosis": "Common Cold",
            "recommendations": "Rest for 2 days",
            "follow_up_required": False,
            "follow_up_date": None,
            "created_at": now,
            "updated_at": now,
        }
        consultation = ConsultationInDB.from_mongo(raw)
        assert consultation.id == "507f1f77bcf86cd799439060"
        assert consultation.appointment_id == "507f1f77bcf86cd799439050"
        assert consultation.patient_id == "507f1f77bcf86cd799439001"
        assert consultation.doctor_id == "507f1f77bcf86cd799439010"


class TestPrescriptionModel:
    def test_create_prescription(self):
        meds = [
            Medication(
                drug_name="Paracetamol",
                dosage="500mg",
                frequency="three times a day",
                duration="3 days"
            )
        ]
        prescription = PrescriptionCreate(
            consultation_id="507f1f77bcf86cd799439060",
            patient_id="507f1f77bcf86cd799439001",
            doctor_id="507f1f77bcf86cd799439010",
            medications=meds,
            dosage_instructions="Take after meals",
            notes="Avoid cold drinks"
        )
        assert len(prescription.medications) == 1
        assert prescription.medications[0].drug_name == "Paracetamol"
        assert prescription.dosage_instructions == "Take after meals"

    def test_prescription_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439070"),
            "consultation_id": ObjectId("507f1f77bcf86cd799439060"),
            "patient_id": ObjectId("507f1f77bcf86cd799439001"),
            "doctor_id": ObjectId("507f1f77bcf86cd799439010"),
            "medications": [
                {
                    "drug_name": "Ibuprofen",
                    "dosage": "400mg",
                    "frequency": "twice daily",
                    "duration": "5 days"
                }
            ],
            "dosage_instructions": "Take with food",
            "notes": None,
            "created_at": now,
            "updated_at": now,
        }
        prescription = PrescriptionInDB.from_mongo(raw)
        assert prescription.id == "507f1f77bcf86cd799439070"
        assert prescription.consultation_id == "507f1f77bcf86cd799439060"
        assert len(prescription.medications) == 1
        assert prescription.medications[0].drug_name == "Ibuprofen"
