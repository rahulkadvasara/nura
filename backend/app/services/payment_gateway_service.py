"""
Nura - Payment Gateway Service
Integrates with the Razorpay Python SDK to create payment orders.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Any

import razorpay

from app.core.config import settings
from app.models.payment import (
    PaymentCreate,
    PaymentInDB,
    PaymentStatus,
    PaymentMethod,
)
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus as AppPaymentStatus
from app.repositories.payment_repository import PaymentRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.services.base import BaseService
from app.services.payment_service import PaymentService
from app.schemas.observability import AuditLogCreateSchema

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class PaymentGatewayService(BaseService[PaymentInDB, PaymentCreate, Any]):
    """Service for payment gateway operations (Razorpay order creation)"""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        appointment_repository: AppointmentRepository,
        audit_log_service: Any,
    ):
        super().__init__()
        self.payment_repository = payment_repository
        self.appointment_repository = appointment_repository
        self.audit_log_service = audit_log_service
        
        # Initialize Razorpay Client
        self.razorpay_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

    async def create_payment_order(
        self,
        appointment_id: str,
        current_user_id: str,
    ) -> Tuple[PaymentInDB, AppointmentInDB]:
        """
        Creates a payment order for the appointment, integrating with Razorpay.
        """
        # 1. Appointment Validation
        appointment = await self.appointment_repository.get(appointment_id)
        if not appointment:
            raise ValueError("Appointment request not found")

        # 2. Authorization Patient check
        if appointment.patient_id != current_user_id:
            raise PermissionError("Unauthorized patient access to appointment")

        # 3. Status checks: Must be APPROVED
        if appointment.status != AppointmentStatus.APPROVED:
            if appointment.status == AppointmentStatus.CANCELLED:
                raise ValueError("Cannot pay for a cancelled appointment")
            elif appointment.status == AppointmentStatus.COMPLETED:
                raise ValueError("Cannot pay for a completed appointment")
            else:
                raise ValueError("Appointment is not approved for payment")

        # 4. Check if already paid
        if appointment.payment_status in (AppPaymentStatus.COMPLETED, AppPaymentStatus.APPROVED):
            raise ValueError("Appointment has already been paid")

        # 5. Prevent duplicate pending payment orders
        existing_orders = await self.payment_repository.get_many({
            "appointment_id": appointment_id,
            "payment_status": {"$in": [PaymentStatus.CREATED, PaymentStatus.PENDING]}
        })
        if existing_orders:
            raise ValueError("A pending payment order already exists for this appointment")

        # 6. Amount validation
        amount = appointment.consultation_fee
        if amount <= 0:
            raise ValueError("Invalid appointment consultation fee amount")

        # 7. Create Razorpay Order (async thread)
        # Note: Razorpay amount is in paise (1 INR = 100 paise)
        amount_in_paise = int(round(amount * 100))
        
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f"receipt_{appointment_id}",
            "notes": {
                "appointment_id": appointment_id,
                "patient_id": appointment.patient_id,
                "doctor_id": appointment.doctor_id,
            }
        }

        try:
            razorpay_order = await asyncio.to_thread(
                self.razorpay_client.order.create,
                order_data
            )
        except Exception as exc:
            logger.exception("Failed to create Razorpay order")
            raise RuntimeError(f"Payment gateway communication failure: {str(exc)}") from exc

        razorpay_order_id = razorpay_order.get("id")
        if not razorpay_order_id:
            raise RuntimeError("Failed to retrieve Razorpay Order ID from gateway response")

        # 8. Store the Payment Order with status = CREATED
        doctor_amount, platform_fee = PaymentService.calculate_revenue_split(amount)
        now = utc_now()
        
        payment_create = PaymentCreate(
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            amount=amount,
            platform_fee=platform_fee,
            doctor_amount=doctor_amount,
            currency="INR",
            payment_method=PaymentMethod.RAZORPAY,
            payment_status=PaymentStatus.CREATED,
            transaction_reference=None,
            escrow_held=False,
            razorpay_order_id=razorpay_order_id,
        )

        doc_dict = payment_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.payment_repository.collection.insert_one(doc_dict)
        created_payment = await self.payment_repository.collection.find_one({"_id": result.inserted_id})
        if not created_payment:
            raise RuntimeError("Payment order was stored but could not be retrieved")

        payment_record = PaymentInDB.from_mongo(created_payment)

        # 9. Audit Event: PAYMENT_ORDER_CREATED
        try:
            audit_schema = AuditLogCreateSchema(
                user_id=current_user_id,
                action="PAYMENT_ORDER_CREATED",
                resource_type="payments",
                resource_id=payment_record.id,
                old_value=None,
                new_value={
                    "appointment_id": appointment_id,
                    "razorpay_order_id": razorpay_order_id,
                    "amount": amount,
                }
            )
            await self.audit_log_service.create_log(audit_schema)
        except Exception:
            logger.exception("Failed to write audit log for payment order creation")

        return payment_record, appointment
