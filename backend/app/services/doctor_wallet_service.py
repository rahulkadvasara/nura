"""
Nura - Doctor Wallet Service
Business logic and validation for doctor wallets
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.payment import (
    DoctorWalletCreate,
    DoctorWalletUpdate,
    DoctorWalletInDB,
)
from app.models.user import UserRole
from app.schemas.payment import (
    DoctorWalletCreateSchema,
    DoctorWalletUpdateSchema,
    DoctorWalletResponse,
)
from app.repositories.doctor_wallet_repository import DoctorWalletRepository
from app.repositories.user_repository import UserRepository
from app.repositories.doctor_repository import DoctorProfileRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _wallet_to_response(wallet: DoctorWalletInDB) -> DoctorWalletResponse:
    return DoctorWalletResponse(
        id=wallet.id,
        doctor_id=wallet.doctor_id,
        total_earned=wallet.total_earned,
        total_withdrawn=wallet.total_withdrawn,
        available_balance=wallet.available_balance,
        pending_balance=wallet.pending_balance,
        last_payout_at=wallet.last_payout_at,
        created_at=wallet.created_at,
        updated_at=wallet.updated_at,
    )


class DoctorWalletService(BaseService[DoctorWalletInDB, DoctorWalletCreate, DoctorWalletUpdate]):
    """Service layer for doctor wallet operations"""

    def __init__(
        self,
        doctor_wallet_repository: DoctorWalletRepository,
        user_repository: UserRepository,
        doctor_profile_repository: Optional[DoctorProfileRepository] = None,
    ):
        super().__init__()
        self.doctor_wallet_repository = doctor_wallet_repository
        self.user_repository = user_repository
        self.doctor_profile_repository = doctor_profile_repository

    async def create_wallet(
        self,
        schema: DoctorWalletCreateSchema,
    ) -> DoctorWalletInDB:
        """Create a new doctor wallet record after validating doctor user / profile existence"""
        # Validate doctor exists
        doctor_user = await self.user_repository.get(schema.doctor_id)
        if doctor_user:
            if doctor_user.role != UserRole.DOCTOR:
                raise ValueError(f"User with ID {schema.doctor_id} is not a doctor")
        elif self.doctor_profile_repository:
            doctor_profile = await self.doctor_profile_repository.get(schema.doctor_id)
            if not doctor_profile:
                raise ValueError(f"Doctor with ID {schema.doctor_id} does not exist")
        else:
            raise ValueError(f"Doctor with ID {schema.doctor_id} does not exist")

        # Prevent duplicate wallets
        existing = await self.doctor_wallet_repository.get_by_doctor_id(schema.doctor_id)
        if existing:
            raise ValueError(f"Wallet already exists for doctor with ID {schema.doctor_id}")

        now = utc_now()
        wallet_create = DoctorWalletCreate(
            doctor_id=schema.doctor_id,
            total_earned=0.0,
            total_withdrawn=0.0,
            available_balance=0.0,
            pending_balance=0.0,
            last_payout_at=None,
        )

        doc_dict = wallet_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.doctor_wallet_repository.collection.insert_one(doc_dict)
        created = await self.doctor_wallet_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Wallet was inserted but could not be retrieved")
        return DoctorWalletInDB.from_mongo(created)

    async def get_wallet_by_id(self, wallet_id: str) -> Optional[DoctorWalletInDB]:
        """Fetch a doctor wallet by its ID"""
        return await self.doctor_wallet_repository.get(wallet_id)

    async def get_wallet_by_doctor_id(self, doctor_id: str) -> Optional[DoctorWalletInDB]:
        """Fetch a doctor wallet by the owning doctor ID"""
        return await self.doctor_wallet_repository.get_by_doctor_id(doctor_id)

    async def list_wallets(self, limit: int = 100, skip: int = 0) -> List[DoctorWalletInDB]:
        """List all doctor wallets"""
        return await self.doctor_wallet_repository.list(limit=limit, skip=skip)

    async def update_wallet(
        self,
        wallet_id: str,
        schema: DoctorWalletUpdateSchema,
    ) -> Optional[DoctorWalletInDB]:
        """Update wallet balances or payout details"""
        update = DoctorWalletUpdate(**schema.model_dump(exclude_unset=True))
        return await self.doctor_wallet_repository.update(wallet_id, update)

    async def delete_wallet(self, wallet_id: str) -> bool:
        """Permanently delete a wallet record"""
        return await self.doctor_wallet_repository.delete(wallet_id)

    def to_response(self, wallet: DoctorWalletInDB) -> DoctorWalletResponse:
        """Convert internal model to API response"""
        return _wallet_to_response(wallet)
