"""
Nura - Appointment Repository
MongoDB repository for appointments collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.appointment import AppointmentCreate, AppointmentUpdate, AppointmentInDB
from app.repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[AppointmentInDB, AppointmentCreate, AppointmentUpdate]):
    """Repository for appointments collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, AppointmentInDB)

    async def get_by_id(self, id: str) -> Optional[AppointmentInDB]:
        """Fetch an appointment by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[AppointmentInDB]:
        """List all appointments"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_patient_id(self, patient_id: str, limit: int = 100, skip: int = 0) -> List[AppointmentInDB]:
        """Fetch all appointments for a given patient"""
        return await self.get_many({"patient_id": patient_id}, limit=limit, skip=skip)

    async def get_by_doctor_id(self, doctor_id: str, limit: int = 100, skip: int = 0) -> List[AppointmentInDB]:
        """Fetch all appointments for a given doctor"""
        return await self.get_many({"doctor_id": doctor_id}, limit=limit, skip=skip)
