"""
Nura - Prescription Service
Business logic and validation for prescriptions
"""

from datetime import datetime, timezone
from typing import List, Optional, Any

from app.models.appointment import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionInDB,
    Medication,
)
from app.schemas.appointment import (
    PrescriptionCreateSchema,
    PrescriptionCreateRequestSchema,
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
            instructions=getattr(m, "instructions", None),
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
        event_dispatcher = None,
    ):
        super().__init__()
        self.prescription_repository = prescription_repository
        self.consultation_repository = consultation_repository
        
        # Lazy load or use injected event dispatcher to prevent circular imports
        if event_dispatcher is None:
            try:
                from app.core.dependencies import get_event_dispatcher
                self.event_dispatcher = get_event_dispatcher()
            except ImportError:
                self.event_dispatcher = None
        else:
            self.event_dispatcher = event_dispatcher

    async def create_prescription(
        self,
        consultation_id: str,
        doctor_profile_id: str,
        doctor_user_id: str,
        schema: PrescriptionCreateRequestSchema,
        notification_service: Any,
        audit_log_service: Any,
        user_repository: Any,
    ) -> PrescriptionInDB:
        """Create a new prescription after validating consultation and duplicate checks"""
        # 1. Validate consultation exists
        consultation = await self.consultation_repository.get(consultation_id)
        if not consultation:
            raise ValueError(f"Consultation with ID {consultation_id} does not exist")

        # 2. Verify consultation belongs to this doctor
        if consultation.doctor_id != doctor_profile_id:
            raise ValueError("Consultation does not belong to this doctor")

        # 3. Check for duplicates (one prescription per consultation)
        existing = await self.prescription_repository.get_by_consultation_id(consultation_id)
        if existing:
            raise ValueError(f"A prescription has already been created for consultation {consultation_id}")

        now = utc_now()
        medications_list = [
            Medication(
                drug_name=med.drug_name,
                dosage=med.dosage,
                frequency=med.frequency,
                duration=med.duration,
                instructions=med.instructions,
            )
            for med in schema.medications
        ]

        prescription_create = PrescriptionCreate(
            consultation_id=consultation_id,
            patient_id=consultation.patient_id,
            doctor_id=doctor_profile_id,
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
        prescription = PrescriptionInDB.from_mongo(created)

        # 4. Resolve doctor name for notification
        doctor_name = "Doctor"
        doctor_user = await user_repository.get(doctor_user_id)
        if doctor_user:
            doctor_name = doctor_user.full_name

        # 5. Create notification for the patient
        try:
            from app.schemas.notification import NotificationCreateSchema
            from app.models.notification import NotificationType, NotificationPriority
            notif_schema = NotificationCreateSchema(
                user_id=consultation.patient_id,
                notification_type=NotificationType.PRESCRIPTION_CREATED,
                title="New Prescription Created",
                message=f"Dr. {doctor_name} has created a prescription for your consultation.",
                priority=NotificationPriority.MEDIUM,
                related_entity_type="prescription",
                related_entity_id=prescription.id,
            )
            await notification_service.create_notification(notif_schema)
        except Exception:
            pass

        # 6. Create Audit Log
        try:
            from app.schemas.observability import AuditLogCreateSchema
            audit_schema = AuditLogCreateSchema(
                user_id=doctor_user_id,
                action="prescription_created",
                resource_type="prescriptions",
                resource_id=prescription.id,
                new_value={"consultation_id": consultation_id, "patient_id": consultation.patient_id},
            )
            await audit_log_service.create_log(audit_schema)
        except Exception:
            pass

        # Dispatch event
        if self.event_dispatcher:
            try:
                from app.events.base import PrescriptionCreatedEvent
                event = PrescriptionCreatedEvent(
                    patient_id=prescription.patient_id,
                    prescription_id=prescription.id,
                    doctor_id=prescription.doctor_id
                )
                await self.event_dispatcher.dispatch(event)
            except Exception as e:
                import logging
                logging.getLogger("nura.services.prescription").error(f"Failed to dispatch PrescriptionCreatedEvent: {e}")

        return prescription

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
        doctor_profile_id: str,
        doctor_user_id: str,
        schema: PrescriptionUpdateSchema,
        appointment_repository: Any,
        audit_log_service: Any,
    ) -> Optional[PrescriptionInDB]:
        """Update an existing prescription only if the associated consultation is completed"""
        prescription = await self.prescription_repository.get(prescription_id)
        if not prescription:
            raise ValueError(f"Prescription with ID {prescription_id} does not exist")

        # Verify prescription belongs to this doctor
        if prescription.doctor_id != doctor_profile_id:
            raise ValueError("Prescription does not belong to this doctor")

        # Fetch associated consultation and appointment
        consultation = await self.consultation_repository.get(prescription.consultation_id)
        if not consultation:
            raise ValueError(f"Associated consultation {prescription.consultation_id} not found")

        appointment = await appointment_repository.get(consultation.appointment_id)
        if not appointment or appointment.status != "completed":
            raise ValueError("Prescription can only be updated while the consultation is completed")

        now = utc_now()
        meds_update = None
        if schema.medications is not None:
            meds_update = [
                Medication(
                    drug_name=m.drug_name,
                    dosage=m.dosage,
                    frequency=m.frequency,
                    duration=m.duration,
                    instructions=m.instructions,
                )
                for m in schema.medications
            ]

        # Prepare update document
        update_data = {}
        if meds_update is not None:
            update_data["medications"] = [m.model_dump() for m in meds_update]
        if schema.dosage_instructions is not None:
            update_data["dosage_instructions"] = schema.dosage_instructions
        if schema.notes is not None:
            update_data["notes"] = schema.notes
        update_data["updated_at"] = now

        # Convert to model to call base repository update if possible, or perform update directly
        update_model = PrescriptionUpdate(
            medications=meds_update,
            dosage_instructions=schema.dosage_instructions,
            notes=schema.notes
        )
        updated = await self.prescription_repository.update(prescription_id, update_model)
        if not updated:
            raise RuntimeError("Failed to update prescription")

        # Create Audit Log
        try:
            from app.schemas.observability import AuditLogCreateSchema
            audit_schema = AuditLogCreateSchema(
                user_id=doctor_user_id,
                action="prescription_updated",
                resource_type="prescriptions",
                resource_id=prescription_id,
                new_value={"updated_at": now.isoformat()},
            )
            await audit_log_service.create_log(audit_schema)
        except Exception:
            pass

        # Dispatch event
        if updated and self.event_dispatcher:
            try:
                from app.events.base import PrescriptionUpdatedEvent
                event = PrescriptionUpdatedEvent(
                    patient_id=updated.patient_id,
                    prescription_id=updated.id,
                    doctor_id=updated.doctor_id
                )
                await self.event_dispatcher.dispatch(event)
            except Exception as e:
                import logging
                logging.getLogger("nura.services.prescription").error(f"Failed to dispatch PrescriptionUpdatedEvent: {e}")

        return updated

    async def delete_prescription(self, prescription_id: str) -> bool:
        """Permanently delete a prescription"""
        return await self.prescription_repository.delete(prescription_id)

    def to_response(self, prescription: PrescriptionInDB) -> PrescriptionResponse:
        """Convert internal model to API response"""
        return _prescription_to_response(prescription)
