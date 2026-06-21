"""
Nura - Prescription Service
Business logic and validation for prescriptions
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.appointment import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionInDB,
    Medication,
)
from app.schemas.appointment import (
    PrescriptionCreateSchema,
    PrescriptionUpdateSchema,
    PrescriptionResponse,
    MedicationSchema,
)
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _prescription_to_response(prescription: PrescriptionInDB) -> PrescriptionResponse:
    # Convert internal medications list to schemas List[MedicationSchema]
    meds = [
        MedicationSchema(
            drug_name=m.drug_name,
            dosage=m.dosage,
            frequency=m.frequency,
            duration=m.duration,
        )
        for m in prescription.medications
    ]
    return PrescriptionResponse(
        id=prescription.id,
        consultation_id=prescription.consultation_id,
        patient_id=prescription.patient_id,
        doctor_id=prescription.doctor_id,
        medications=meds,
        dosage_instructions=prescription.dosage_instructions,
        notes=prescription.notes,
        created_at=prescription.created_at,
        updated_at=prescription.updated_at,
    )


class PrescriptionService(BaseService[PrescriptionInDB, PrescriptionCreate, PrescriptionUpdate]):
    """Service layer for prescription operations"""

    def __init__(
        self,
        prescription_repository: PrescriptionRepository,
        consultation_repository: ConsultationRepository,
    ):
        super().__init__()
        self.prescription_repository = prescription_repository
        self.consultation_repository = consultation_repository

    async def create_prescription(
        self,
        schema: PrescriptionCreateSchema,
    ) -> PrescriptionInDB:
        """Create a new prescription after validating consultation existence"""
        # Validate consultation exists
        consultation = await self.consultation_repository.get(schema.consultation_id)
        if not consultation:
            raise ValueError(f"Consultation with ID {schema.consultation_id} does not exist")

        now = utc_now()
        medications_list = [
            Medication(
                drug_name=med.drug_name,
                dosage=med.dosage,
                frequency=med.frequency,
                duration=med.duration,
            )
            for med in schema.medications
        ]

        prescription_create = PrescriptionCreate(
            consultation_id=schema.consultation_id,
            patient_id=schema.patient_id,
            doctor_id=schema.doctor_id,
            medications=medications_list,
            dosage_instructions=schema.dosage_instructions,
            notes=schema.notes,
        )

        doc_dict = prescription_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.prescription_repository.collection.insert_one(doc_dict)
        created = await self.prescription_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Prescription was inserted but could not be retrieved")
        return PrescriptionInDB.from_mongo(created)

    async def get_prescription_by_id(self, prescription_id: str) -> Optional[PrescriptionInDB]:
        """Fetch prescription by its ID"""
        return await self.prescription_repository.get(prescription_id)

    async def get_prescription_by_consultation(self, consultation_id: str) -> Optional[PrescriptionInDB]:
        """Fetch prescription associated with consultation"""
        return await self.prescription_repository.get_by_consultation_id(consultation_id)

    async def list_prescriptions(self, limit: int = 100, skip: int = 0) -> List[PrescriptionInDB]:
        """List all prescriptions"""
        return await self.prescription_repository.list(limit=limit, skip=skip)

    async def list_prescriptions_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[PrescriptionInDB]:
        """Fetch all prescriptions for a patient"""
        return await self.prescription_repository.get_by_patient_id(patient_id, limit=limit, skip=skip)

    async def list_prescriptions_by_doctor(
        self,
        doctor_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[PrescriptionInDB]:
        """Fetch all prescriptions for a doctor"""
        return await self.prescription_repository.get_by_doctor_id(doctor_id, limit=limit, skip=skip)

    async def update_prescription(
        self,
        prescription_id: str,
        schema: PrescriptionUpdateSchema,
    ) -> Optional[PrescriptionInDB]:
        """Update an existing prescription"""
        update = PrescriptionUpdate(**schema.model_dump(exclude_unset=True))
        return await self.prescription_repository.update(prescription_id, update)

    async def delete_prescription(self, prescription_id: str) -> bool:
        """Permanently delete a prescription"""
        return await self.prescription_repository.delete(prescription_id)

    def to_response(self, prescription: PrescriptionInDB) -> PrescriptionResponse:
        """Convert internal model to API response"""
        return _prescription_to_response(prescription)
