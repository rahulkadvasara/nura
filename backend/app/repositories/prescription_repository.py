"""
Nura - Prescription Repository
MongoDB repository for prescriptions collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.appointment import PrescriptionCreate, PrescriptionUpdate, PrescriptionInDB
from app.repositories.base import BaseRepository


class PrescriptionRepository(BaseRepository[PrescriptionInDB, PrescriptionCreate, PrescriptionUpdate]):
    """Repository for prescriptions collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, PrescriptionInDB)

    async def get_by_id(self, id: str) -> Optional[PrescriptionInDB]:
        """Fetch a prescription by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[PrescriptionInDB]:
        """List all prescriptions"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_consultation_id(self, consultation_id: str) -> Optional[PrescriptionInDB]:
        """Fetch a prescription by its associated consultation ID"""
        return await self.get_by_filter({"consultation_id": consultation_id})

    async def get_by_patient_id(self, patient_id: str, limit: int = 100, skip: int = 0) -> List[PrescriptionInDB]:
        """Fetch all prescriptions for a given patient"""
        return await self.get_many({"patient_id": patient_id}, limit=limit, skip=skip)

    async def get_by_doctor_id(self, doctor_id: str, limit: int = 100, skip: int = 0) -> List[PrescriptionInDB]:
        """Fetch all prescriptions for a given doctor"""
        return await self.get_many({"doctor_id": doctor_id}, limit=limit, skip=skip)
