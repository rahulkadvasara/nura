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
    ):
        super().__init__()
        self.reminder_repository = reminder_repository
        self.user_repository = user_repository

    async def create_reminder(
        self,
        schema: ReminderCreateSchema,
    ) -> ReminderInDB:
        """Create a new reminder record after validating patient user existence"""
        # Validate patient exists
        patient = await self.user_repository.get(schema.patient_id)
        if not patient:
            raise ValueError(f"Patient user with ID {schema.patient_id} does not exist")

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
        return ReminderInDB.from_mongo(created)

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
        update = ReminderUpdate(**schema.model_dump(exclude_unset=True))
        return await self.reminder_repository.update(reminder_id, update)

    async def delete_reminder(self, reminder_id: str) -> bool:
        """Permanently delete a reminder record"""
        return await self.reminder_repository.delete(reminder_id)

    def to_response(self, reminder: ReminderInDB) -> ReminderResponse:
        """Convert internal model to API response"""
        return _reminder_to_response(reminder)
