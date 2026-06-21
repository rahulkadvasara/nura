"""
Nura - Payment and Wallet Services Tests
Unit tests for PaymentService and DoctorWalletService using mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
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
from app.schemas.payment import (
    PaymentCreateSchema,
    PaymentUpdateSchema,
    PaymentResponse,
    DoctorWalletCreateSchema,
    DoctorWalletUpdateSchema,
)
from app.services.payment_service import PaymentService
from app.services.doctor_wallet_service import DoctorWalletService


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


@pytest.fixture
def sample_payment():
    return PaymentInDB(
        id="507f1f77bcf86cd799439080",
        appointment_id="507f1f77bcf86cd799439010",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439002",
        amount=500.0,
        platform_fee=75.0,
        doctor_amount=425.0,
        currency="INR",
        payment_method=PaymentMethod.UPI,
        payment_status=PaymentStatus.PENDING,
        transaction_reference="ref_abc",
        escrow_held=False,
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


class TestPaymentService:
    def test_revenue_split_calculation(self):
        # 100 split: Doctor (85), Platform (15)
        doc, plat = PaymentService.calculate_revenue_split(100.0)
        assert doc == 85.0
        assert plat == 15.0

        # Float split: total 49.99
        doc, plat = PaymentService.calculate_revenue_split(49.99)
        assert doc == round(49.99 * 0.85, 2)
        assert doc + plat == 49.99

    @pytest.mark.asyncio
    async def test_create_payment_success(self, sample_patient_user, sample_doctor_user, sample_appointment):
        pay_repo = AsyncMock()
        pay_repo.collection = MagicMock()
        pay_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439080"))
        )
        pay_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "appointment_id": sample_appointment.id,
            "patient_id": sample_patient_user.id,
            "doctor_id": sample_doctor_user.id,
            "amount": 500.0,
            "platform_fee": 75.0,
            "doctor_amount": 425.0,
            "currency": "INR",
            "payment_method": "upi",
            "payment_status": "pending",
            "escrow_held": False,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })

        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)

        user_repo = AsyncMock()
        # Mock get returning patient user first, then doctor user
        user_repo.get = AsyncMock(side_effect=[sample_patient_user, sample_doctor_user])

        service = PaymentService(pay_repo, app_repo, user_repo)
        schema = PaymentCreateSchema(
            appointment_id=sample_appointment.id,
            patient_id=sample_patient_user.id,
            doctor_id=sample_doctor_user.id,
            amount=500.0,
            payment_method=PaymentMethod.UPI,
        )

        result = await service.create_payment(schema)
        assert isinstance(result, PaymentInDB)
        assert result.id == "507f1f77bcf86cd799439080"
        assert result.platform_fee == 75.0
        assert result.doctor_amount == 425.0
        app_repo.get.assert_called_once_with(sample_appointment.id)

    @pytest.mark.asyncio
    async def test_create_payment_appointment_not_found(self):
        pay_repo = AsyncMock()
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=None)
        user_repo = AsyncMock()

        service = PaymentService(pay_repo, app_repo, user_repo)
        schema = PaymentCreateSchema(
            appointment_id="invalid_app",
            patient_id="pat_1",
            doctor_id="doc_1",
            amount=100.0,
            payment_method=PaymentMethod.UPI,
        )

        with pytest.raises(ValueError, match="Appointment with ID.*does not exist"):
            await service.create_payment(schema)

    @pytest.mark.asyncio
    async def test_create_payment_patient_not_found(self, sample_appointment):
        pay_repo = AsyncMock()
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None)

        service = PaymentService(pay_repo, app_repo, user_repo)
        schema = PaymentCreateSchema(
            appointment_id=sample_appointment.id,
            patient_id="invalid_patient",
            doctor_id="doc_1",
            amount=100.0,
            payment_method=PaymentMethod.UPI,
        )

        with pytest.raises(ValueError, match="Patient user with ID.*does not exist"):
            await service.create_payment(schema)

    @pytest.mark.asyncio
    async def test_create_payment_doctor_not_found(self, sample_appointment, sample_patient_user):
        pay_repo = AsyncMock()
        app_repo = AsyncMock()
        app_repo.get = AsyncMock(return_value=sample_appointment)
        user_repo = AsyncMock()
        # patient user exists, doctor user does not
        user_repo.get = AsyncMock(side_effect=[sample_patient_user, None])

        service = PaymentService(pay_repo, app_repo, user_repo)
        schema = PaymentCreateSchema(
            appointment_id=sample_appointment.id,
            patient_id=sample_patient_user.id,
            doctor_id="invalid_doctor",
            amount=100.0,
            payment_method=PaymentMethod.UPI,
        )

        with pytest.raises(ValueError, match="Doctor with ID.*does not exist"):
            await service.create_payment(schema)


class TestDoctorWalletService:
    @pytest.mark.asyncio
    async def test_create_wallet_success(self, sample_doctor_user):
        wallet_repo = AsyncMock()
        wallet_repo.get_by_doctor_id = AsyncMock(return_value=None) # No existing wallet
        wallet_repo.collection = MagicMock()
        wallet_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439090"))
        )
        wallet_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "doctor_id": sample_doctor_user.id,
            "total_earned": 0.0,
            "total_withdrawn": 0.0,
            "available_balance": 0.0,
            "pending_balance": 0.0,
            "last_payout_at": None,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_doctor_user)

        service = DoctorWalletService(wallet_repo, user_repo)
        schema = DoctorWalletCreateSchema(doctor_id=sample_doctor_user.id)

        result = await service.create_wallet(schema)
        assert isinstance(result, DoctorWalletInDB)
        assert result.doctor_id == sample_doctor_user.id
        user_repo.get.assert_called_once_with(sample_doctor_user.id)
        wallet_repo.get_by_doctor_id.assert_called_once_with(sample_doctor_user.id)

    @pytest.mark.asyncio
    async def test_create_wallet_doctor_not_found(self):
        wallet_repo = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None)

        service = DoctorWalletService(wallet_repo, user_repo)
        schema = DoctorWalletCreateSchema(doctor_id="invalid_doctor")

        with pytest.raises(ValueError, match="Doctor with ID.*does not exist"):
            await service.create_wallet(schema)

    @pytest.mark.asyncio
    async def test_create_wallet_already_exists(self, sample_doctor_user, sample_wallet):
        wallet_repo = AsyncMock()
        wallet_repo.get_by_doctor_id = AsyncMock(return_value=sample_wallet)
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_doctor_user)

        service = DoctorWalletService(wallet_repo, user_repo)
        schema = DoctorWalletCreateSchema(doctor_id=sample_doctor_user.id)

        with pytest.raises(ValueError, match="Wallet already exists for doctor"):
            await service.create_wallet(schema)
