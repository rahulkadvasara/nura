"""
Nura - Payment and Wallet Repositories Tests
Unit tests for PaymentRepository and DoctorWalletRepository using mocked MongoDB collections.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentInDB,
    PaymentStatus,
    PaymentMethod,
    DoctorWalletCreate,
    DoctorWalletUpdate,
    DoctorWalletInDB,
)
from app.repositories.payment_repository import PaymentRepository
from app.repositories.doctor_wallet_repository import DoctorWalletRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_payment_doc(
    payment_id: str = "507f1f77bcf86cd799439080",
    appointment_id: str = "507f1f77bcf86cd799439001",
    patient_id: str = "507f1f77bcf86cd799439002",
    doctor_id: str = "507f1f77bcf86cd799439003",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(payment_id),
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "amount": 500.0,
        "platform_fee": 75.0,
        "doctor_amount": 425.0,
        "currency": "INR",
        "payment_method": "upi",
        "payment_status": "pending",
        "transaction_reference": None,
        "escrow_held": False,
        "created_at": now,
        "updated_at": now,
    }


def make_wallet_doc(
    wallet_id: str = "507f1f77bcf86cd799439090",
    doctor_id: str = "507f1f77bcf86cd799439003",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(wallet_id),
        "doctor_id": doctor_id,
        "total_earned": 0.0,
        "total_withdrawn": 0.0,
        "available_balance": 0.0,
        "pending_balance": 0.0,
        "last_payout_at": None,
        "created_at": now,
        "updated_at": now,
    }


def make_mock_collection(find_one_return=None, find_return=None, update_result=None):
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)

    insert_result = MagicMock()
    insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439080")
    collection.insert_one = AsyncMock(return_value=insert_result)

    upd_result = MagicMock()
    upd_result.modified_count = 1 if update_result is None else update_result
    collection.update_one = AsyncMock(return_value=upd_result)

    del_result = MagicMock()
    del_result.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=del_result)

    cursor = MagicMock()
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=find_return or [])
    collection.find = MagicMock(return_value=cursor)

    return collection


class TestPaymentRepository:
    @pytest.mark.asyncio
    async def test_create_payment(self):
        doc = make_payment_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = PaymentRepository(collection)

        payment_create = PaymentCreate(
            appointment_id="507f1f77bcf86cd799439001",
            patient_id="507f1f77bcf86cd799439002",
            doctor_id="507f1f77bcf86cd799439003",
            amount=500.0,
            platform_fee=75.0,
            doctor_amount=425.0,
            payment_method=PaymentMethod.UPI,
        )
        result = await repo.create(payment_create)
        assert isinstance(result, PaymentInDB)
        assert result.amount == 500.0
        assert result.doctor_amount == 425.0

    @pytest.mark.asyncio
    async def test_get_payment(self):
        doc = make_payment_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = PaymentRepository(collection)

        result = await repo.get_by_id("507f1f77bcf86cd799439080")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439080"

    @pytest.mark.asyncio
    async def test_get_by_patient_id(self):
        docs = [make_payment_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = PaymentRepository(collection)

        results = await repo.get_by_patient_id("507f1f77bcf86cd799439002")
        assert len(results) == 1
        assert results[0].patient_id == "507f1f77bcf86cd799439002"

    @pytest.mark.asyncio
    async def test_get_by_doctor_id(self):
        docs = [make_payment_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = PaymentRepository(collection)

        results = await repo.get_by_doctor_id("507f1f77bcf86cd799439003")
        assert len(results) == 1
        assert results[0].doctor_id == "507f1f77bcf86cd799439003"

    @pytest.mark.asyncio
    async def test_update_payment(self):
        updated_doc = make_payment_doc()
        updated_doc["payment_status"] = "approved"
        collection = make_mock_collection(find_one_return=updated_doc)
        repo = PaymentRepository(collection)

        update = PaymentUpdate(payment_status=PaymentStatus.APPROVED)
        result = await repo.update("507f1f77bcf86cd799439080", update)
        assert result is not None
        assert result.payment_status == PaymentStatus.APPROVED

    @pytest.mark.asyncio
    async def test_delete_payment(self):
        collection = make_mock_collection()
        repo = PaymentRepository(collection)
        result = await repo.delete("507f1f77bcf86cd799439080")
        assert result is True

    @pytest.mark.asyncio
    async def test_list_payments(self):
        docs = [make_payment_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = PaymentRepository(collection)

        results = await repo.list()
        assert len(results) == 1


class TestDoctorWalletRepository:
    @pytest.mark.asyncio
    async def test_create_wallet(self):
        doc = make_wallet_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = DoctorWalletRepository(collection)

        wallet_create = DoctorWalletCreate(
            doctor_id="507f1f77bcf86cd799439003",
        )
        result = await repo.create(wallet_create)
        assert isinstance(result, DoctorWalletInDB)
        assert result.doctor_id == "507f1f77bcf86cd799439003"

    @pytest.mark.asyncio
    async def test_get_wallet_by_doctor_id(self):
        doc = make_wallet_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = DoctorWalletRepository(collection)

        result = await repo.get_by_doctor_id("507f1f77bcf86cd799439003")
        assert result is not None
        assert result.doctor_id == "507f1f77bcf86cd799439003"
        collection.find_one.assert_called_once_with({"doctor_id": "507f1f77bcf86cd799439003"})
