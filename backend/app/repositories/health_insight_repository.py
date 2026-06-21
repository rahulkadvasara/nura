"""
Nura - Health Insight Repository
MongoDB repository for health_insights collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.report import HealthInsightCreate, HealthInsightUpdate, HealthInsightInDB
from app.repositories.base import BaseRepository


class HealthInsightRepository(BaseRepository[HealthInsightInDB, HealthInsightCreate, HealthInsightUpdate]):
    """Repository for health_insights collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, HealthInsightInDB)

    async def get_by_id(self, id: str) -> Optional[HealthInsightInDB]:
        """Fetch a health insight by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[HealthInsightInDB]:
        """List all health insights"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_patient_id(self, patient_id: str, limit: int = 100, skip: int = 0) -> List[HealthInsightInDB]:
        """Fetch all health insights for a given patient"""
        return await self.get_many({"patient_id": patient_id}, limit=limit, skip=skip)
