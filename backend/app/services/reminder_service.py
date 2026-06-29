"""
Nura - Reminder Service
Business logic and validation for patient reminders
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.reminder import (
    ReminderCreate,
    ReminderUpdate,
    ReminderInDB,
    ReminderStatus,
    ReminderType,
)
from app.schemas.reminder import (
    ReminderCreateSchema,
    ReminderUpdateSchema,
    ReminderResponse,
)
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _reminder_to_response(reminder: ReminderInDB) -> ReminderResponse:
    return ReminderResponse(
        id=reminder.id,
        patient_id=reminder.patient_id,
        reminder_type=reminder.reminder_type,
        title=reminder.title,
        description=reminder.description,
        scheduled_time=reminder.scheduled_time,
        recurrence=reminder.recurrence,
        status=reminder.status,
        source_type=reminder.source_type,
        source_id=reminder.source_id,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )


class ReminderService(BaseService[ReminderInDB, ReminderCreate, ReminderUpdate]):
    """Service layer for patient reminder operations"""

    def __init__(
        self,
        reminder_repository: ReminderRepository,
        user_repository: UserRepository,
        event_dispatcher = None,
    ):
        super().__init__()
        self.reminder_repository = reminder_repository
        self.user_repository = user_repository
        
        # Lazy load or use injected event dispatcher to prevent circular imports
        if event_dispatcher is None:
            try:
                from app.core.dependencies import get_event_dispatcher
                self.event_dispatcher = get_event_dispatcher()
            except ImportError:
                self.event_dispatcher = None
        else:
            self.event_dispatcher = event_dispatcher

    async def create_reminder(
        self,
        schema: ReminderCreateSchema,
    ) -> ReminderInDB:
        """Create a new reminder record after validating patient user existence"""
        # Validate patient exists
        patient = await self.user_repository.get(schema.patient_id)
        if not patient:
            raise ValueError(f"Patient user with ID {schema.patient_id} does not exist")

        # Drug Safety checks for medication reminder
        if schema.reminder_type == ReminderType.MEDICATION:
            from app.core.dependencies import get_medication_validation_service
            validation_service = get_medication_validation_service()
            
            # Clean title
            title = schema.title or ""
            clean_name = title.strip()
            if clean_name.lower().startswith("take "):
                clean_name = clean_name[5:].strip()
                
            # Perform validation
            val_res = await validation_service.validate_medications(
                patient_id=schema.patient_id,
                incoming_medications=[clean_name],
                source="reminder",
                override_reason=schema.override_reason if schema.override else None,
                overridden_by=schema.user_role if schema.override else None
            )
            
            if val_res.get("decision") == "BLOCK":
                is_override_authorized = schema.override and schema.user_role in ("doctor", "admin")
                if not is_override_authorized:
                    raise ValueError(
                        f"Medication reminder creation blocked due to critical interaction: "
                        f"{val_res.get('recommendations', ['Critical risk interaction'])[0]}. "
                        f"Requires authorized doctor/admin override."
                    )
            
            # Re-evaluate the patient's full active list and update validation_summary inside patient_memory
            await validation_service.validate_and_update_patient_memory(schema.patient_id)

        now = utc_now()
        reminder_create = ReminderCreate(
            patient_id=schema.patient_id,
            reminder_type=schema.reminder_type,
            title=schema.title,
            description=schema.description,
            scheduled_time=schema.scheduled_time,
            recurrence=schema.recurrence,
            status=schema.status,
            source_type=schema.source_type,
            source_id=schema.source_id,
        )

        doc_dict = reminder_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.reminder_repository.collection.insert_one(doc_dict)
        created = await self.reminder_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Reminder was inserted but could not be retrieved")
            
        reminder_obj = ReminderInDB.from_mongo(created)
        
        # Dispatch event
        if self.event_dispatcher:
            try:
                from app.events.base import ReminderCreatedEvent
                event = ReminderCreatedEvent(
                    patient_id=reminder_obj.patient_id,
                    reminder_id=reminder_obj.id
                )
                await self.event_dispatcher.dispatch(event)
            except Exception as e:
                import logging
                logging.getLogger("nura.services.reminder").error(f"Failed to dispatch ReminderCreatedEvent: {e}")

        return reminder_obj

    async def get_reminder_by_id(self, reminder_id: str) -> Optional[ReminderInDB]:
        """Fetch a reminder by its ID"""
        return await self.reminder_repository.get(reminder_id)

    async def list_reminders(self, limit: int = 100, skip: int = 0) -> List[ReminderInDB]:
        """List all reminders"""
        return await self.reminder_repository.list(limit=limit, skip=skip)

    async def list_reminders_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[ReminderInDB]:
        """Fetch all reminders for a patient"""
        return await self.reminder_repository.get_by_patient_id(patient_id, limit=limit, skip=skip)

    async def list_active_reminders(
        self,
        patient_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[ReminderInDB]:
        """Fetch all active reminders, optionally filtered by patient ID"""
        return await self.reminder_repository.get_active_reminders(patient_id, limit=limit, skip=skip)

    async def update_reminder(
        self,
        reminder_id: str,
        schema: ReminderUpdateSchema,
    ) -> Optional[ReminderInDB]:
        """Update an existing reminder record"""
        existing = await self.reminder_repository.get(reminder_id)
        if not existing:
            return None
            
        patient_id = existing.patient_id
        rem_type = schema.reminder_type or existing.reminder_type
        title = schema.title or existing.title
        
        if rem_type == ReminderType.MEDICATION:
            from app.core.dependencies import get_medication_validation_service
            validation_service = get_medication_validation_service()
            
            clean_name = title.strip()
            if clean_name.lower().startswith("take "):
                clean_name = clean_name[5:].strip()
                
            val_res = await validation_service.validate_medications(
                patient_id=patient_id,
                incoming_medications=[clean_name],
                source="reminder",
                override_reason=schema.override_reason if schema.override else None,
                overridden_by=schema.user_role if schema.override else None
            )
            
            if val_res.get("decision") == "BLOCK":
                is_override_authorized = schema.override and schema.user_role in ("doctor", "admin")
                if not is_override_authorized:
                    raise ValueError(
                        f"Medication reminder update blocked due to critical interaction. "
                        f"Requires authorized doctor/admin override."
                    )
            
            # Re-evaluate memory
            await validation_service.validate_and_update_patient_memory(patient_id)

        update = ReminderUpdate(**schema.model_dump(exclude_unset=True))
        updated_reminder = await self.reminder_repository.update(reminder_id, update)
        
        # Dispatch event
        if updated_reminder and self.event_dispatcher:
            try:
                from app.events.base import ReminderUpdatedEvent
                event = ReminderUpdatedEvent(
                    patient_id=updated_reminder.patient_id,
                    reminder_id=updated_reminder.id
                )
                await self.event_dispatcher.dispatch(event)
            except Exception as e:
                import logging
                logging.getLogger("nura.services.reminder").error(f"Failed to dispatch ReminderUpdatedEvent: {e}")
                
        return updated_reminder

    async def delete_reminder(self, reminder_id: str) -> bool:
        """Permanently delete a reminder record"""
        existing = await self.reminder_repository.get(reminder_id)
        success = await self.reminder_repository.delete(reminder_id)
        if success and existing:
            try:
                from app.core.dependencies import get_medication_validation_service
                validation_service = get_medication_validation_service()
                await validation_service.validate_and_update_patient_memory(existing.patient_id)
            except Exception as e:
                logger.error(f"Failed to update patient memory validation summary on reminder deletion: {e}")
        return success

    def to_response(self, reminder: ReminderInDB) -> ReminderResponse:
        """Convert internal model to API response"""
        return _reminder_to_response(reminder)
