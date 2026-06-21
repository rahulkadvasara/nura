"""
Nura - Payment Repository
MongoDB repository for payments collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.payment import PaymentCreate, PaymentUpdate, PaymentInDB
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[PaymentInDB, PaymentCreate, PaymentUpdate]):
    """Repository for payments collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, PaymentInDB)

    async def get_by_id(self, id: str) -> Optional[PaymentInDB]:
        """Fetch a payment record by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[PaymentInDB]:
        """List all payment records"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_patient_id(self, patient_id: str, limit: int = 100, skip: int = 0) -> List[PaymentInDB]:
        """Fetch all payments for a given patient"""
        return await self.get_many({"patient_id": patient_id}, limit=limit, skip=skip)

    async def get_by_doctor_id(self, doctor_id: str, limit: int = 100, skip: int = 0) -> List[PaymentInDB]:
        """Fetch all payments for a given doctor"""
        return await self.get_many({"doctor_id": doctor_id}, limit=limit, skip=skip)
