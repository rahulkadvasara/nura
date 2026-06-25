"""
Nura - Payment Gateway Service Tests
Unit tests for PaymentGatewayService covering order creation, verification, and wallets.
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
    DoctorWalletInDB,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
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
def sample_doctor_user():
    return UserInDB(
        id="507f1f77bcf86cd799439002",
        role=UserRole.DOCTOR,
        email="doctor@example.com",
        password_hash="hashed_pw",
        full_name="Doctor Name",
        phone="0987654321",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_doctor_profile():
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439003",
        user_id="507f1f77bcf86cd799439002",
        specialization="Cardiology",
        qualifications=["MD"],
        experience_years=10,
        consultation_fee=500.0,
        bio="Cardiology expert.",
        languages=["English"],
        hospital="Clinic B",
        license_number="LIC-12345",
        profile_status=DoctorProfileStatus.VERIFIED,
        average_rating=5.0,
        total_reviews=1,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_appointment():
    return AppointmentInDB(
        id="507f1f77bcf86cd799439010",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439003",  # Doctor profile ID
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


@pytest.fixture
def sample_payment():
    return PaymentInDB(
        id="507f1f77bcf86cd799439080",
        appointment_id="507f1f77bcf86cd799439010",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439002",  # Doctor user ID
        amount=500.0,
        platform_fee=75.0,
        doctor_amount=425.0,
        currency="INR",
        payment_method=PaymentMethod.RAZORPAY,
        payment_status=PaymentStatus.CREATED,
        razorpay_order_id="order_test_123",
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_wallet():
    return DoctorWalletInDB(
        id="507f1f77bcf86cd799439090",
        doctor_id="507f1f77bcf86cd799439002",
        total_earned=0.0,
        total_withdrawn=0.0,
        available_balance=0.0,
        pending_balance=0.0,
        last_payout_at=None,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


class TestPaymentGatewayService:

    @pytest.mark.asyncio
    @patch("razorpay.Client")
    async def test_create_payment_order_success(
        self, mock_razorpay_client, sample_patient_user, sample_doctor_profile, sample_appointment
    ):
        pay_repo = AsyncMock()
        pay_repo.get_many = AsyncMock(return_value=[])
        pay_repo.collection = MagicMock()
        pay_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439080"))
        )
        pay_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "appointment_id": sample_appointment.id,
            "patient_id": sample_patient_user.id,
            "doctor_id": sample_doctor_profile.user_id,
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

        doc_profile_repo = AsyncMock()
        doc_profile_repo.get = AsyncMock(return_value=sample_doctor_profile)

        doc_wallet_repo = AsyncMock()
        notif_service = AsyncMock()
        user_repo = AsyncMock()
        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            doctor_profile_repository=doc_profile_repo,
            doctor_wallet_repository=doc_wallet_repo,
            notification_service=notif_service,
            user_repository=user_repo,
            audit_log_service=audit_service,
        )

        service.razorpay_client.order.create = MagicMock(return_value={"id": "order_test_123"})

        payment, appt = await service.create_payment_order(
            appointment_id=sample_appointment.id,
            current_user_id=sample_patient_user.id,
        )

        assert isinstance(payment, PaymentInDB)
        assert payment.payment_status == PaymentStatus.CREATED
        assert payment.razorpay_order_id == "order_test_123"
        assert payment.doctor_id == sample_doctor_profile.user_id
        
        assert app_repo.get.call_count == 2
        app_repo.get.assert_any_call(sample_appointment.id)
        doc_profile_repo.get.assert_called_once_with(sample_appointment.doctor_id)
        audit_service.create_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_payment_order_unauthorized_patient(self, sample_appointment):
        pay_repo = AsyncMock()
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        
        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            doctor_profile_repository=AsyncMock(),
            doctor_wallet_repository=AsyncMock(),
            notification_service=AsyncMock(),
            user_repository=AsyncMock(),
            audit_log_service=AsyncMock(),
        )

        with pytest.raises(PermissionError, match="Unauthorized patient access"):
            await service.create_payment_order(
                appointment_id=sample_appointment.id,
                current_user_id="different_patient_id",
            )

    @pytest.mark.asyncio
    @patch("razorpay.Client")
    async def test_verify_payment_success(
        self, mock_razorpay_client, sample_patient_user, sample_doctor_user, sample_appointment, sample_payment, sample_wallet
    ):
        # Ensure sample_payment starts as CREATED
        sample_payment.payment_status = PaymentStatus.CREATED
        
        import copy
        success_payment = copy.deepcopy(sample_payment)
        success_payment.payment_status = PaymentStatus.SUCCESS

        pay_repo = AsyncMock()
        pay_repo.get_by_filter = AsyncMock(return_value=sample_payment)
        pay_repo.update = AsyncMock(return_value=success_payment)
        pay_repo.get_many = AsyncMock(return_value=[])

        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        app_repo.update = AsyncMock()

        doc_profile_repo = AsyncMock()
        # Mock profile
        doc_profile = DoctorProfileInDB(
            id="507f1f77bcf86cd799439003",
            user_id=sample_doctor_user.id,
            specialization="Cardiology",
            qualifications=["MD"],
            experience_years=10,
            consultation_fee=500.0,
            bio="Bio",
            languages=["English"],
            profile_status=DoctorProfileStatus.VERIFIED,
            average_rating=5.0,
            total_reviews=1,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        doc_profile_repo.get = AsyncMock(return_value=doc_profile)

        doc_wallet_repo = AsyncMock()
        doc_wallet_repo.get_by_doctor_id = AsyncMock(return_value=sample_wallet)
        doc_wallet_repo.update = AsyncMock()

        notif_service = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(side_effect=[sample_doctor_user, sample_patient_user])
        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            doctor_profile_repository=doc_profile_repo,
            doctor_wallet_repository=doc_wallet_repo,
            notification_service=notif_service,
            user_repository=user_repo,
            audit_log_service=audit_service,
        )

        # Mock verify signature success
        service.razorpay_client.utility.verify_payment_signature = MagicMock(return_value=True)

        payload = {
            "razorpay_payment_id": "pay_test_123",
            "razorpay_order_id": "order_test_123",
            "razorpay_signature": "sig_test_123",
        }

        payment, appt, wallet_summary, revenue_split = await service.verify_payment(
            payload=payload,
            current_user_id=sample_patient_user.id,
        )

        assert payment.payment_status == PaymentStatus.SUCCESS
        assert app_repo.update.called
        assert doc_wallet_repo.update.called
        assert audit_service.create_log.call_count == 3  # verified, wallet, split
        assert notif_service.create_notification.call_count == 2  # patient, doctor
        
        # Verify wallet summary updates
        assert wallet_summary["previous_available_balance"] == 0.0
        assert wallet_summary["new_available_balance"] == 425.0
        assert revenue_split["doctor_share"] == 425.0
        assert revenue_split["platform_share"] == 75.0

    @pytest.mark.asyncio
    @patch("razorpay.Client")
    async def test_verify_payment_invalid_signature(
        self, mock_razorpay_client, sample_patient_user, sample_payment
    ):
        pay_repo = AsyncMock()
        pay_repo.get_by_filter = AsyncMock(return_value=sample_payment)
        pay_repo.get_many = AsyncMock(return_value=[])
        
        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=AsyncMock(),
            doctor_profile_repository=AsyncMock(),
            doctor_wallet_repository=AsyncMock(),
            notification_service=AsyncMock(),
            user_repository=AsyncMock(),
            audit_log_service=AsyncMock(),
        )

        # Mock verify signature failure
        service.razorpay_client.utility.verify_payment_signature = MagicMock(
            side_effect=Exception("Signature mismatch")
        )

        payload = {
            "razorpay_payment_id": "pay_test_123",
            "razorpay_order_id": "order_test_123",
            "razorpay_signature": "invalid_sig",
        }

        with pytest.raises(ValueError, match="Invalid payment signature"):
            await service.verify_payment(
                payload=payload,
                current_user_id=sample_patient_user.id,
            )

    @pytest.mark.asyncio
    @patch("razorpay.Client")
    async def test_verify_payment_idempotency(
        self, mock_razorpay_client, sample_patient_user, sample_payment, sample_appointment, sample_wallet
    ):
        # Set status to SUCCESS to simulate prior successful verification
        sample_payment.payment_status = PaymentStatus.SUCCESS

        pay_repo = AsyncMock()
        pay_repo.get_by_filter = AsyncMock(return_value=sample_payment)
        pay_repo.update = AsyncMock()
        pay_repo.get_many = AsyncMock(return_value=[])

        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        app_repo.update = AsyncMock()

        doc_wallet_repo = AsyncMock()
        doc_wallet_repo.get_by_doctor_id = AsyncMock(return_value=sample_wallet)

        audit_service = AsyncMock()
        notif_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            doctor_profile_repository=AsyncMock(),
            doctor_wallet_repository=doc_wallet_repo,
            notification_service=notif_service,
            user_repository=AsyncMock(),
            audit_log_service=audit_service,
        )

        payload = {
            "razorpay_payment_id": "pay_test_123",
            "razorpay_order_id": "order_test_123",
            "razorpay_signature": "sig_test_123",
        }

        payment, appt, wallet_summary, revenue_split = await service.verify_payment(
            payload=payload,
            current_user_id=sample_patient_user.id,
        )

        # Verify no database updates, audits or notifications were triggered
        assert payment.payment_status == PaymentStatus.SUCCESS
        assert not pay_repo.update.called
        assert not app_repo.update.called
        assert not audit_service.create_log.called
        assert not notif_service.create_notification.called

    @pytest.mark.asyncio
    async def test_fail_payment_success(self, sample_patient_user, sample_payment, sample_appointment):
        pay_repo = AsyncMock()
        pay_repo.get = AsyncMock(return_value=sample_payment)
        
        failed_payment = sample_payment.model_copy(update={"payment_status": PaymentStatus.FAILED})
        pay_repo.update = AsyncMock(return_value=failed_payment)

        app_repo = AsyncMock()
        app_repo.update = AsyncMock()

        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            doctor_profile_repository=AsyncMock(),
            doctor_wallet_repository=AsyncMock(),
            notification_service=AsyncMock(),
            user_repository=AsyncMock(),
            audit_log_service=audit_service,
        )

        result = await service.fail_payment(
            payment_id=sample_payment.id,
            current_user_id=sample_patient_user.id,
            error_details={"code": "BAD_REQUEST", "description": "Closed by user"}
        )

        assert result.payment_status == PaymentStatus.FAILED
        pay_repo.update.assert_called_once()
        app_repo.update.assert_called_once()
        
        # Verify PAYMENT_FAILED audit logged
        audit_service.create_log.assert_called_once()
        assert audit_service.create_log.call_args[0][0].action == "PAYMENT_FAILED"

    @pytest.mark.asyncio
    async def test_cancel_payment_success(self, sample_patient_user, sample_payment, sample_appointment):
        pay_repo = AsyncMock()
        pay_repo.get = AsyncMock(return_value=sample_payment)
        
        cancelled_payment = sample_payment.model_copy(update={"payment_status": PaymentStatus.CANCELLED})
        pay_repo.update = AsyncMock(return_value=cancelled_payment)

        app_repo = AsyncMock()
        app_repo.update = AsyncMock()

        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            doctor_profile_repository=AsyncMock(),
            doctor_wallet_repository=AsyncMock(),
            notification_service=AsyncMock(),
            user_repository=AsyncMock(),
            audit_log_service=audit_service,
        )

        result = await service.cancel_payment(
            payment_id=sample_payment.id,
            current_user_id=sample_patient_user.id
        )

        assert result.payment_status == PaymentStatus.CANCELLED
        pay_repo.update.assert_called_once()
        app_repo.update.assert_called_once()
        
        # Verify PAYMENT_CANCELLED audit logged
        audit_service.create_log.assert_called_once()
        assert audit_service.create_log.call_args[0][0].action == "PAYMENT_CANCELLED"

    @pytest.mark.asyncio
    @patch("razorpay.Client")
    async def test_create_payment_order_retry(
        self, mock_razorpay_client, sample_patient_user, sample_doctor_profile, sample_appointment, sample_payment
    ):
        # Existing failed payment
        sample_payment.payment_status = PaymentStatus.FAILED
        
        pay_repo = AsyncMock()
        async def mock_get_many(q):
            in_list = q.get("payment_status", {}).get("$in", [])
            if PaymentStatus.SUCCESS in in_list or PaymentStatus.CREATED in in_list:
                return []
            if PaymentStatus.FAILED in in_list:
                return [sample_payment]
            return []
        pay_repo.get_many = AsyncMock(side_effect=mock_get_many)
        pay_repo.collection = MagicMock()
        pay_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439080"))
        )
        pay_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "appointment_id": sample_appointment.id,
            "patient_id": sample_patient_user.id,
            "doctor_id": sample_doctor_profile.user_id,
            "amount": 500.0,
            "platform_fee": 75.0,
            "doctor_amount": 425.0,
            "currency": "INR",
            "payment_method": "razorpay",
            "payment_status": "created",
            "razorpay_order_id": "order_test_retry_123",
            "escrow_held": False,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })

        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        app_repo.update = AsyncMock()

        doc_profile_repo = AsyncMock()
        doc_profile_repo.get = AsyncMock(return_value=sample_doctor_profile)

        audit_service = AsyncMock()

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            doctor_profile_repository=doc_profile_repo,
            doctor_wallet_repository=AsyncMock(),
            notification_service=AsyncMock(),
            user_repository=AsyncMock(),
            audit_log_service=audit_service,
        )

        service.razorpay_client.order.create = MagicMock(return_value={"id": "order_test_retry_123"})

        payment, appt = await service.create_payment_order(
            appointment_id=sample_appointment.id,
            current_user_id=sample_patient_user.id,
        )

        assert payment.razorpay_order_id == "order_test_retry_123"
        # Verify PAYMENT_RETRY_CREATED audit was logged
        audit_service.create_log.assert_called_once()
        assert audit_service.create_log.call_args[0][0].action == "PAYMENT_RETRY_CREATED"

    @pytest.mark.asyncio
    @patch("razorpay.Client")
    async def test_create_payment_order_idempotent_duplicate(
        self, mock_razorpay_client, sample_patient_user, sample_appointment, sample_payment
    ):
        # Existing created order
        sample_payment.payment_status = PaymentStatus.CREATED
        
        pay_repo = AsyncMock()
        async def mock_get_many(q):
            in_list = q.get("payment_status", {}).get("$in", [])
            if PaymentStatus.SUCCESS in in_list:
                return []
            if PaymentStatus.CREATED in in_list:
                return [sample_payment]
            return []
        pay_repo.get_many = AsyncMock(side_effect=mock_get_many)

        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)

        service = PaymentGatewayService(
            payment_repository=pay_repo,
            appointment_repository=app_repo,
            doctor_profile_repository=AsyncMock(),
            doctor_wallet_repository=AsyncMock(),
            notification_service=AsyncMock(),
            user_repository=AsyncMock(),
            audit_log_service=AsyncMock(),
        )

        # Call create order and verify it returns existing instead of throwing an error
        payment, appt = await service.create_payment_order(
            appointment_id=sample_appointment.id,
            current_user_id=sample_patient_user.id
        )

        assert payment.id == sample_payment.id
        assert payment.payment_status == PaymentStatus.CREATED
        # Ensure Razorpay client create was NOT called
        assert not mock_razorpay_client.return_value.order.create.called

