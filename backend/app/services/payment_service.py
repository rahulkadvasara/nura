"""
Nura - Payment Service
Business logic, validation, and revenue split calculations for payments
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.models.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentInDB,
    PaymentStatus,
    PaymentMethod,
)
from app.models.user import UserRole
from app.schemas.payment import (
    PaymentCreateSchema,
    PaymentUpdateSchema,
    PaymentResponse,
)
from app.repositories.payment_repository import PaymentRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.doctor_repository import DoctorProfileRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _payment_to_response(payment: PaymentInDB) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        appointment_id=payment.appointment_id,
        patient_id=payment.patient_id,
        doctor_id=payment.doctor_id,
        amount=payment.amount,
        platform_fee=payment.platform_fee,
        doctor_amount=payment.doctor_amount,
        currency=payment.currency,
        payment_method=payment.payment_method,
        payment_status=payment.payment_status,
        transaction_reference=payment.transaction_reference,
        escrow_held=payment.escrow_held,
        razorpay_order_id=payment.razorpay_order_id,
        escrow_released_at=payment.escrow_released_at,
        escrow_released_by=payment.escrow_released_by,
        refunded_at=payment.refunded_at,
        refund_reason=payment.refund_reason,
        analytics_metadata=payment.analytics_metadata,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


class PaymentService(BaseService[PaymentInDB, PaymentCreate, PaymentUpdate]):
    """Service layer for payment operations"""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        appointment_repository: AppointmentRepository,
        user_repository: UserRepository,
        doctor_profile_repository: Optional[DoctorProfileRepository] = None,
    ):
        super().__init__()
        self.payment_repository = payment_repository
        self.appointment_repository = appointment_repository
        self.user_repository = user_repository
        self.doctor_profile_repository = doctor_profile_repository

    @staticmethod
    def calculate_revenue_split(amount: float) -> Tuple[float, float]:
        """
        Calculate the 85/15 revenue split.
        Doctor receives 85%, Platform receives 15%.
        To prevent floating point mismatches, doctor's amount is rounded first,
        and platform fee takes the remainder.
        """
        doctor_amount = round(amount * 0.85, 2)
        platform_fee = round(amount - doctor_amount, 2)
        return doctor_amount, platform_fee

    async def create_payment(
        self,
        schema: PaymentCreateSchema,
    ) -> PaymentInDB:
        """Create a new payment record after validating appointment, patient, and doctor existence"""
        # Validate appointment exists
        appointment = await self.appointment_repository.get(schema.appointment_id)
        if not appointment:
            raise ValueError(f"Appointment with ID {schema.appointment_id} does not exist")

        # Validate patient exists and has PATIENT role
        patient = await self.user_repository.get(schema.patient_id)
        if not patient:
            raise ValueError(f"Patient user with ID {schema.patient_id} does not exist")
        if patient.role != UserRole.PATIENT:
            raise ValueError(f"User with ID {schema.patient_id} is not a patient")

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

        now = utc_now()
        doctor_amount, platform_fee = self.calculate_revenue_split(schema.amount)

        payment_create = PaymentCreate(
            appointment_id=schema.appointment_id,
            patient_id=schema.patient_id,
            doctor_id=schema.doctor_id,
            amount=schema.amount,
            platform_fee=platform_fee,
            doctor_amount=doctor_amount,
            currency=schema.currency,
            payment_method=schema.payment_method,
            payment_status=PaymentStatus.PENDING,
            transaction_reference=schema.transaction_reference,
            escrow_held=schema.escrow_held,
            razorpay_order_id=schema.razorpay_order_id,
            analytics_metadata=schema.analytics_metadata or {},
        )

        doc_dict = payment_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.payment_repository.collection.insert_one(doc_dict)
        created = await self.payment_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Payment was inserted but could not be retrieved")
        return PaymentInDB.from_mongo(created)

    async def get_payment_by_id(self, payment_id: str) -> Optional[PaymentInDB]:
        """Fetch a payment record by its ID"""
        return await self.payment_repository.get(payment_id)

    async def list_payments(self, limit: int = 100, skip: int = 0) -> List[PaymentInDB]:
        """List all payment records"""
        return await self.payment_repository.list(limit=limit, skip=skip)

    async def list_payments_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[PaymentInDB]:
        """Fetch all payments for a patient"""
        return await self.payment_repository.get_by_patient_id(patient_id, limit=limit, skip=skip)

    async def list_payments_by_doctor(
        self,
        doctor_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[PaymentInDB]:
        """Fetch all payments for a doctor"""
        return await self.payment_repository.get_by_doctor_id(doctor_id, limit=limit, skip=skip)

    async def update_payment(
        self,
        payment_id: str,
        schema: PaymentUpdateSchema,
    ) -> Optional[PaymentInDB]:
        """Update an existing payment record"""
        update = PaymentUpdate(**schema.model_dump(exclude_unset=True))
        return await self.payment_repository.update(payment_id, update)

    async def delete_payment(self, payment_id: str) -> bool:
        """Permanently delete a payment record"""
        return await self.payment_repository.delete(payment_id)

    def to_response(self, payment: PaymentInDB) -> PaymentResponse:
        """Convert internal model to API response"""
        return _payment_to_response(payment)
