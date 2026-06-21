"""
Nura - Appointment Service
Business logic and validation for appointments
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentInDB,
    AppointmentStatus,
    PaymentStatus,
)
from app.schemas.appointment import (
    AppointmentCreateSchema,
    AppointmentUpdateSchema,
    AppointmentResponse,
)
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_repository import DoctorProfileRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _appointment_to_response(appointment: AppointmentInDB) -> AppointmentResponse:
    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        slot_date=appointment.slot_date,
        slot_time=appointment.slot_time,
        duration_minutes=appointment.duration_minutes,
        consultation_fee=appointment.consultation_fee,
        status=appointment.status,
        payment_status=appointment.payment_status,
        notes=appointment.notes,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )


class AppointmentService(BaseService[AppointmentInDB, AppointmentCreate, AppointmentUpdate]):
    """Service layer for appointment operations"""

    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        doctor_profile_repository: DoctorProfileRepository,
        user_repository: UserRepository,
    ):
        super().__init__()
        self.appointment_repository = appointment_repository
        self.doctor_profile_repository = doctor_profile_repository
        self.user_repository = user_repository

    async def create_appointment(
        self,
        patient_id: str,
        schema: AppointmentCreateSchema,
    ) -> AppointmentInDB:
        """Create a new appointment after validating patient and doctor existence"""
        # Validate patient exists
        patient = await self.user_repository.get(patient_id)
        if not patient:
            raise ValueError(f"Patient user with ID {patient_id} does not exist")

        # Validate doctor exists
        doctor = await self.doctor_profile_repository.get(schema.doctor_id)
        if not doctor:
            raise ValueError(f"Doctor profile with ID {schema.doctor_id} does not exist")

        now = utc_now()
        appointment_create = AppointmentCreate(
            patient_id=patient_id,
            doctor_id=schema.doctor_id,
            slot_date=schema.slot_date,
            slot_time=schema.slot_time,
            duration_minutes=schema.duration_minutes,
            consultation_fee=schema.consultation_fee,
            status=AppointmentStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            notes=schema.notes,
        )

        doc_dict = appointment_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.appointment_repository.collection.insert_one(doc_dict)
        created = await self.appointment_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Appointment was inserted but could not be retrieved")
        return AppointmentInDB.from_mongo(created)

    async def get_appointment_by_id(self, appointment_id: str) -> Optional[AppointmentInDB]:
        """Fetch appointment by its ID"""
        return await self.appointment_repository.get(appointment_id)

    async def list_appointments(self, limit: int = 100, skip: int = 0) -> List[AppointmentInDB]:
        """List all appointments"""
        return await self.appointment_repository.list(limit=limit, skip=skip)

    async def list_appointments_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[AppointmentInDB]:
        """Fetch all appointments for a patient"""
        return await self.appointment_repository.get_by_patient_id(patient_id, limit=limit, skip=skip)

    async def list_appointments_by_doctor(
        self,
        doctor_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[AppointmentInDB]:
        """Fetch all appointments for a doctor"""
        return await self.appointment_repository.get_by_doctor_id(doctor_id, limit=limit, skip=skip)

    async def update_appointment(
        self,
        appointment_id: str,
        schema: AppointmentUpdateSchema,
    ) -> Optional[AppointmentInDB]:
        """Update an existing appointment. If doctor_id is updated, validate it."""
        if schema.doctor_id is not None:
            doctor = await self.doctor_profile_repository.get(schema.doctor_id)
            if not doctor:
                raise ValueError(f"Doctor profile with ID {schema.doctor_id} does not exist")

        update = AppointmentUpdate(**schema.model_dump(exclude_unset=True))
        return await self.appointment_repository.update(appointment_id, update)

    async def delete_appointment(self, appointment_id: str) -> bool:
        """Permanently delete an appointment"""
        return await self.appointment_repository.delete(appointment_id)

    def to_response(self, appointment: AppointmentInDB) -> AppointmentResponse:
        """Convert internal model to API response"""
        return _appointment_to_response(appointment)
