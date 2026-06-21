"""
Nura - Report Repository
MongoDB repository for reports collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.report import ReportCreate, ReportUpdate, ReportInDB
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[ReportInDB, ReportCreate, ReportUpdate]):
    """Repository for reports collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, ReportInDB)

    async def get_by_id(self, id: str) -> Optional[ReportInDB]:
        """Fetch a report by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[ReportInDB]:
        """List all reports"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_patient_id(self, patient_id: str, limit: int = 100, skip: int = 0) -> List[ReportInDB]:
        """Fetch all reports for a given patient"""
        return await self.get_many({"patient_id": patient_id}, limit=limit, skip=skip)
