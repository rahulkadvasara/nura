"""
Nura - Payment Gateway Service Tests
Unit tests for PaymentGatewayService covering validation rules and Razorpay integration.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from app.models.payment import (
    PaymentInDB,
    PaymentStatus,
    PaymentMethod,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus as AppPaymentStatus
from app.services.payment_gateway_service import PaymentGatewayService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_patient_user():
    return UserInDB(
        id="507f1f77bcf86cd799439001",
        role=UserRole.PATIENT,
        email="patient@example.com",
        password_hash="hashed_pw",
        full_name="Patient Name",
        phone="1234567890",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_appointment():
    return AppointmentInDB(
        id="507f1f77bcf86cd799439010",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439002",
        slot_date="2026-06-25",
        slot_time="10:00",
        duration_minutes=30,
        consultation_fee=500.0,
        status=AppointmentStatus.APPROVED,
        payment_status=AppPaymentStatus.PENDING,
        notes="Urgent",
        created_at=utc_now(),
        updated_at=utc_now(),
    )


class TestPaymentGatewayService:

    @pytest.mark.asyncio
    @patch("razorpay.Client")
    async def test_create_payment_order_success(self, mock_razorpay_client, sample_patient_user, sample_appointment):
        # Mock repositories
        pay_repo = AsyncMock()
        pay_repo.get_many = AsyncMock(return_value=[])  # No duplicate pending orders
        pay_repo.collection = MagicMock()
        pay_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439080"))
        )
        pay_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "appointment_id": sample_appointment.id,
            "patient_id": sample_patient_user.id,
            "doctor_id": "507f1f77bcf86cd799439002",
            "amount": 500.0,
            "platform_fee": 75.0,
            "doctor_amount": 425.0,
            "currency": "INR",
            "payment_method": "razorpay",
            "payment_status": "created",
            "razorpay_order_id": "order_test_123",
            "escrow_held": False,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })

        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)

        audit_service = AsyncMock()

        # Instantiate service
        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            audit_log_service=audit_service,
        )

        # Mock Razorpay API call
        service.razorpay_client.order.create = MagicMock(return_value={"id": "order_test_123"})

        # Run creation
        payment, appt = await service.create_payment_order(
            appointment_id=sample_appointment.id,
            current_user_id=sample_patient_user.id,
        )

        assert isinstance(payment, PaymentInDB)
        assert payment.payment_status == PaymentStatus.CREATED
        assert payment.razorpay_order_id == "order_test_123"
        assert appt.id == sample_appointment.id
        
        # Verify validations and logic were executed
        app_repo.get.assert_called_once_with(sample_appointment.id)
        pay_repo.get_many.assert_called_once()
        audit_service.create_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_payment_order_unauthorized_patient(self, sample_appointment):
        pay_repo = AsyncMock()
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            audit_log_service=audit_service,
        )

        # Try to pay as a different user
        with pytest.raises(PermissionError, match="Unauthorized patient access"):
            await service.create_payment_order(
                appointment_id=sample_appointment.id,
                current_user_id="different_patient_id",
            )

    @pytest.mark.asyncio
    async def test_create_payment_order_invalid_status_pending(self, sample_appointment):
        # Set appointment status to pending (not approved)
        sample_appointment.status = AppointmentStatus.PENDING

        pay_repo = AsyncMock()
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            audit_log_service=audit_service,
        )

        with pytest.raises(ValueError, match="Appointment is not approved for payment"):
            await service.create_payment_order(
                appointment_id=sample_appointment.id,
                current_user_id=sample_appointment.patient_id,
            )

    @pytest.mark.asyncio
    async def test_create_payment_order_invalid_status_cancelled(self, sample_appointment):
        sample_appointment.status = AppointmentStatus.CANCELLED

        pay_repo = AsyncMock()
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            audit_log_service=audit_service,
        )

        with pytest.raises(ValueError, match="Cannot pay for a cancelled appointment"):
            await service.create_payment_order(
                appointment_id=sample_appointment.id,
                current_user_id=sample_appointment.patient_id,
            )

    @pytest.mark.asyncio
    async def test_create_payment_order_already_paid(self, sample_appointment):
        sample_appointment.payment_status = AppPaymentStatus.COMPLETED

        pay_repo = AsyncMock()
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            audit_log_service=audit_service,
        )

        with pytest.raises(ValueError, match="Appointment has already been paid"):
            await service.create_payment_order(
                appointment_id=sample_appointment.id,
                current_user_id=sample_appointment.patient_id,
            )

    @pytest.mark.asyncio
    async def test_create_payment_order_duplicate_pending(self, sample_appointment):
        pay_repo = AsyncMock()
        # Mock existing pending payment order
        pay_repo.get_many = AsyncMock(return_value=[
            PaymentInDB(
                id="507f1f77bcf86cd799439080",
                appointment_id=sample_appointment.id,
                patient_id=sample_appointment.patient_id,
                doctor_id=sample_appointment.doctor_id,
                amount=500.0,
                platform_fee=75.0,
                doctor_amount=425.0,
                currency="INR",
                payment_method=PaymentMethod.RAZORPAY,
                payment_status=PaymentStatus.CREATED,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
        ])
        
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            audit_log_service=audit_service,
        )

        with pytest.raises(ValueError, match="A pending payment order already exists"):
            await service.create_payment_order(
                appointment_id=sample_appointment.id,
                current_user_id=sample_appointment.patient_id,
            )
