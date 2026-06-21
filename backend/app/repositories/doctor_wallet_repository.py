"""
Nura - Doctor Wallet Repository
MongoDB repository for doctor_wallets collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.payment import DoctorWalletCreate, DoctorWalletUpdate, DoctorWalletInDB
from app.repositories.base import BaseRepository


class DoctorWalletRepository(BaseRepository[DoctorWalletInDB, DoctorWalletCreate, DoctorWalletUpdate]):
    """Repository for doctor_wallets collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, DoctorWalletInDB)

    async def get_by_id(self, id: str) -> Optional[DoctorWalletInDB]:
        """Fetch a doctor wallet by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[DoctorWalletInDB]:
        """List all doctor wallets"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_doctor_id(self, doctor_id: str) -> Optional[DoctorWalletInDB]:
        """Fetch the wallet for a given doctor"""
        return await self.get_by_filter({"doctor_id": doctor_id})
