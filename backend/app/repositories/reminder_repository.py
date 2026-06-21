"""
Nura - Reminder Repository
MongoDB repository for reminders collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.reminder import ReminderCreate, ReminderUpdate, ReminderInDB, ReminderStatus
from app.repositories.base import BaseRepository


class ReminderRepository(BaseRepository[ReminderInDB, ReminderCreate, ReminderUpdate]):
    """Repository for reminders collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, ReminderInDB)

    async def get_by_id(self, id: str) -> Optional[ReminderInDB]:
        """Fetch a reminder by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[ReminderInDB]:
        """List all reminders"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_patient_id(self, patient_id: str, limit: int = 100, skip: int = 0) -> List[ReminderInDB]:
        """Fetch all reminders for a given patient"""
        return await self.get_many({"patient_id": patient_id}, limit=limit, skip=skip)

    async def get_active_reminders(self, patient_id: Optional[str] = None, limit: int = 100, skip: int = 0) -> List[ReminderInDB]:
        """Fetch all active reminders, optionally filtered by patient ID"""
        query = {"status": ReminderStatus.ACTIVE}
        if patient_id:
            query["patient_id"] = patient_id
        return await self.get_many(query, limit=limit, skip=skip)
