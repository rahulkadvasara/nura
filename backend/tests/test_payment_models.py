"""
Nura - Payment and Wallet Models Tests
Tests for payments and doctor_wallets Pydantic models
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from app.models.payment import (
    PaymentStatus,
    PaymentMethod,
    PaymentCreate,
    PaymentUpdate,
    PaymentInDB,
    DoctorWalletCreate,
    DoctorWalletUpdate,
    DoctorWalletInDB,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TestPaymentEnums:
    def test_payment_status_values(self):
        assert PaymentStatus.PENDING == "pending"
        assert PaymentStatus.HELD == "held"
        assert PaymentStatus.APPROVED == "approved"
        assert PaymentStatus.COMPLETED == "completed"
        assert PaymentStatus.REFUNDED == "refunded"
        assert PaymentStatus.FAILED == "failed"

    def test_payment_method_values(self):
        assert PaymentMethod.RAZORPAY == "razorpay"
        assert PaymentMethod.CARD == "card"
        assert PaymentMethod.UPI == "upi"
        assert PaymentMethod.NETBANKING == "netbanking"


class TestPaymentModel:
    def test_create_payment(self):
        now = utc_now()
        payment = PaymentCreate(
            appointment_id="507f1f77bcf86cd799439001",
            patient_id="507f1f77bcf86cd799439002",
            doctor_id="507f1f77bcf86cd799439003",
            amount=500.0,
            platform_fee=75.0,
            doctor_amount=425.0,
            currency="INR",
            payment_method=PaymentMethod.UPI,
            payment_status=PaymentStatus.PENDING,
            transaction_reference="ref_123",
            escrow_held=True,
            razorpay_order_id="order_123",
        )
        assert payment.appointment_id == "507f1f77bcf86cd799439001"
        assert payment.patient_id == "507f1f77bcf86cd799439002"
        assert payment.doctor_id == "507f1f77bcf86cd799439003"
        assert payment.amount == 500.0
        assert payment.platform_fee == 75.0
        assert payment.doctor_amount == 425.0
        assert payment.currency == "INR"
        assert payment.payment_method == PaymentMethod.UPI
        assert payment.payment_status == PaymentStatus.PENDING
        assert payment.transaction_reference == "ref_123"
        assert payment.escrow_held is True
        assert payment.razorpay_order_id == "order_123"

    def test_payment_default_values(self):
        payment = PaymentCreate(
            appointment_id="app_1",
            patient_id="pat_1",
            doctor_id="doc_1",
            amount=100.0,
            platform_fee=15.0,
            doctor_amount=85.0,
            payment_method=PaymentMethod.CARD,
        )
        assert payment.currency == "INR"
        assert payment.payment_status == PaymentStatus.PENDING
        assert payment.transaction_reference is None
        assert payment.escrow_held is False
        assert payment.razorpay_order_id is None
        assert payment.escrow_released_at is None
        assert payment.escrow_released_by is None
        assert payment.refunded_at is None
        assert payment.refund_reason is None
        assert payment.analytics_metadata == {}

    def test_payment_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "appointment_id": ObjectId("507f1f77bcf86cd799439001"),
            "patient_id": ObjectId("507f1f77bcf86cd799439002"),
            "doctor_id": ObjectId("507f1f77bcf86cd799439003"),
            "amount": 1000.0,
            "platform_fee": 150.0,
            "doctor_amount": 850.0,
            "currency": "INR",
            "payment_method": "upi",
            "payment_status": "approved",
            "transaction_reference": "ref_999",
            "escrow_held": False,
            "created_at": now,
            "updated_at": now,
        }
        payment = PaymentInDB.from_mongo(raw)
        assert payment.id == "507f1f77bcf86cd799439080"
        assert payment.appointment_id == "507f1f77bcf86cd799439001"
        assert payment.patient_id == "507f1f77bcf86cd799439002"
        assert payment.doctor_id == "507f1f77bcf86cd799439003"
        assert payment.created_at == now


class TestDoctorWalletModel:
    def test_create_wallet(self):
        wallet = DoctorWalletCreate(
            doctor_id="507f1f77bcf86cd799439003",
            total_earned=1000.0,
            total_withdrawn=200.0,
            available_balance=800.0,
            pending_balance=200.0,
        )
        assert wallet.doctor_id == "507f1f77bcf86cd799439003"
        assert wallet.total_earned == 1000.0
        assert wallet.total_withdrawn == 200.0
        assert wallet.available_balance == 800.0
        assert wallet.pending_balance == 200.0

    def test_wallet_default_values(self):
        wallet = DoctorWalletCreate(
            doctor_id="doc_1",
        )
        assert wallet.total_earned == 0.0
        assert wallet.total_withdrawn == 0.0
        assert wallet.available_balance == 0.0
        assert wallet.pending_balance == 0.0
        assert wallet.last_payout_at is None

    def test_wallet_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "doctor_id": ObjectId("507f1f77bcf86cd799439003"),
            "total_earned": 5000.0,
            "total_withdrawn": 1000.0,
            "available_balance": 4000.0,
            "pending_balance": 0.0,
            "last_payout_at": now,
            "created_at": now,
            "updated_at": now,
        }
        wallet = DoctorWalletInDB.from_mongo(raw)
        assert wallet.id == "507f1f77bcf86cd799439080"
        assert wallet.doctor_id == "507f1f77bcf86cd799439003"
        assert wallet.created_at == now
        assert wallet.last_payout_at == now
