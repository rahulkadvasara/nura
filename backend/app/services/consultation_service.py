"""
Nura - Consultation Service
Business logic and validation for consultations
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.appointment import (
    ConsultationCreate,
    ConsultationUpdate,
    ConsultationInDB,
)
from app.schemas.appointment import (
    ConsultationCreateSchema,
    ConsultationUpdateSchema,
    ConsultationResponse,
)
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _consultation_to_response(consultation: ConsultationInDB) -> ConsultationResponse:
    return ConsultationResponse(
        id=consultation.id,
        appointment_id=consultation.appointment_id,
        patient_id=consultation.patient_id,
        doctor_id=consultation.doctor_id,
        consultation_notes=consultation.consultation_notes,
        diagnosis=consultation.diagnosis,
        recommendations=consultation.recommendations,
        follow_up_required=consultation.follow_up_required,
        follow_up_date=consultation.follow_up_date,
        created_at=consultation.created_at,
        updated_at=consultation.updated_at,
    )


class ConsultationService(BaseService[ConsultationInDB, ConsultationCreate, ConsultationUpdate]):
    """Service layer for consultation operations"""

    def __init__(
        self,
        consultation_repository: ConsultationRepository,
        appointment_repository: AppointmentRepository,
    ):
        super().__init__()
        self.consultation_repository = consultation_repository
        self.appointment_repository = appointment_repository

    async def create_consultation(
        self,
        schema: ConsultationCreateSchema,
    ) -> ConsultationInDB:
        """Create a new consultation after validating appointment existence"""
        # Validate appointment exists
        appointment = await self.appointment_repository.get(schema.appointment_id)
        if not appointment:
            raise ValueError(f"Appointment with ID {schema.appointment_id} does not exist")

        now = utc_now()
        consultation_create = ConsultationCreate(
            appointment_id=schema.appointment_id,
            patient_id=schema.patient_id,
            doctor_id=schema.doctor_id,
            consultation_notes=schema.consultation_notes,
            diagnosis=schema.diagnosis,
            recommendations=schema.recommendations,
            follow_up_required=schema.follow_up_required,
            follow_up_date=schema.follow_up_date,
        )

        doc_dict = consultation_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.consultation_repository.collection.insert_one(doc_dict)
        created = await self.consultation_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Consultation was inserted but could not be retrieved")
        return ConsultationInDB.from_mongo(created)

    async def get_consultation_by_id(self, consultation_id: str) -> Optional[ConsultationInDB]:
        """Fetch consultation by its ID"""
        return await self.consultation_repository.get(consultation_id)

    async def get_consultation_by_appointment(self, appointment_id: str) -> Optional[ConsultationInDB]:
        """Fetch consultation associated with appointment"""
        return await self.consultation_repository.get_by_appointment_id(appointment_id)

    async def list_consultations(self, limit: int = 100, skip: int = 0) -> List[ConsultationInDB]:
        """List all consultations"""
        return await self.consultation_repository.list(limit=limit, skip=skip)

    async def list_consultations_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[ConsultationInDB]:
        """Fetch all consultations for a patient"""
        return await self.consultation_repository.get_by_patient_id(patient_id, limit=limit, skip=skip)

    async def list_consultations_by_doctor(
        self,
        doctor_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[ConsultationInDB]:
        """Fetch all consultations for a doctor"""
        return await self.consultation_repository.get_by_doctor_id(doctor_id, limit=limit, skip=skip)

    async def update_consultation(
        self,
        consultation_id: str,
        schema: ConsultationUpdateSchema,
    ) -> Optional[ConsultationInDB]:
        """Update an existing consultation"""
        update = ConsultationUpdate(**schema.model_dump(exclude_unset=True))
        return await self.consultation_repository.update(consultation_id, update)

    async def delete_consultation(self, consultation_id: str) -> bool:
        """Permanently delete a consultation"""
        return await self.consultation_repository.delete(consultation_id)

    def to_response(self, consultation: ConsultationInDB) -> ConsultationResponse:
        """Convert internal model to API response"""
        return _consultation_to_response(consultation)
