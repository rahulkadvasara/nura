"""
Nura - Consultation Repository
MongoDB repository for consultations collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.appointment import ConsultationCreate, ConsultationUpdate, ConsultationInDB
from app.repositories.base import BaseRepository


class ConsultationRepository(BaseRepository[ConsultationInDB, ConsultationCreate, ConsultationUpdate]):
    """Repository for consultations collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, ConsultationInDB)

    async def get_by_id(self, id: str) -> Optional[ConsultationInDB]:
        """Fetch a consultation by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[ConsultationInDB]:
        """List all consultations"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_appointment_id(self, appointment_id: str) -> Optional[ConsultationInDB]:
        """Fetch a consultation by its associated appointment ID"""
        return await self.get_by_filter({"appointment_id": appointment_id})

    async def get_by_patient_id(self, patient_id: str, limit: int = 100, skip: int = 0) -> List[ConsultationInDB]:
        """Fetch all consultations for a given patient"""
        return await self.get_many({"patient_id": patient_id}, limit=limit, skip=skip)

    async def get_by_doctor_id(self, doctor_id: str, limit: int = 100, skip: int = 0) -> List[ConsultationInDB]:
        """Fetch all consultations for a given doctor"""
        return await self.get_many({"doctor_id": doctor_id}, limit=limit, skip=skip)
