"""
Nura - Patient Memory Repository
MongoDB repository for patient_memory collection
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.patient_memory import PatientMemoryCreate, PatientMemoryUpdate, PatientMemoryInDB
from app.repositories.base import BaseRepository


class PatientMemoryRepository(BaseRepository[PatientMemoryInDB, PatientMemoryCreate, PatientMemoryUpdate]):
    """Repository for patient_memory collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, PatientMemoryInDB)

    async def get_by_patient_id(self, patient_id: str) -> Optional[PatientMemoryInDB]:
        """Fetch patient memory record by patient ID"""
        return await self.get_by_filter({"patient_id": patient_id})
