"""
Nura - Payment Gateway Service
Integrates with the Razorpay Python SDK to create and verify payment orders.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Any, Dict

import razorpay
from bson import ObjectId

from app.core.config import settings
from app.models.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentInDB,
    PaymentStatus,
    PaymentMethod,
    DoctorWalletInDB,
)
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus as AppPaymentStatus
from app.repositories.payment_repository import PaymentRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_wallet_repository import DoctorWalletRepository
from app.repositories.doctor_repository import DoctorProfileRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService
from app.services.payment_service import PaymentService
from app.schemas.observability import AuditLogCreateSchema

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class PaymentGatewayService(BaseService[PaymentInDB, PaymentCreate, Any]):
    """Service for payment gateway operations (Razorpay order creation and verification)"""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        appointment_repository: AppointmentRepository,
        doctor_profile_repository: DoctorProfileRepository,
        doctor_wallet_repository: DoctorWalletRepository,
        notification_service: Any,
        user_repository: UserRepository,
        audit_log_service: Any,
    ):
        super().__init__()
        self.payment_repository = payment_repository
        self.appointment_repository = appointment_repository
        self.doctor_profile_repository = doctor_profile_repository
        self.doctor_wallet_repository = doctor_wallet_repository
        self.notification_service = notification_service
        self.user_repository = user_repository
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

        # 4. Check if already paid (Raise ValueError if any successful payment exists)
        successful_payments = await self.payment_repository.get_many({
            "appointment_id": appointment_id,
            "payment_status": {"$in": [PaymentStatus.SUCCESS, PaymentStatus.APPROVED, PaymentStatus.COMPLETED]}
        })
        if successful_payments or appointment.payment_status in (AppPaymentStatus.COMPLETED, AppPaymentStatus.APPROVED, AppPaymentStatus.PAID):
            raise ValueError("Appointment has already been paid")

        # 5. Prevent duplicate pending payment orders (Return existing active order for browser refresh/double-click)
        existing_orders = await self.payment_repository.get_many({
            "appointment_id": appointment_id,
            "payment_status": {"$in": [PaymentStatus.CREATED, PaymentStatus.PENDING]}
        })
        if existing_orders:
            return existing_orders[0], appointment

        # 6. Check if this is a retry (has historical failed or cancelled payments)
        prior_payments = await self.payment_repository.get_many({
            "appointment_id": appointment_id,
            "payment_status": {"$in": [PaymentStatus.FAILED, PaymentStatus.CANCELLED]}
        })
        is_retry = len(prior_payments) > 0

        # 7. Amount validation
        amount = appointment.consultation_fee
        if amount <= 0:
            raise ValueError("Invalid appointment consultation fee amount")

        # Resolve doctor user ID from doctor profile ID
        doctor_profile = await self.doctor_profile_repository.get(appointment.doctor_id)
        if not doctor_profile:
            raise ValueError("Doctor profile associated with appointment not found")
        doctor_user_id = doctor_profile.user_id

        # 8. Create Razorpay Order (async thread)
        amount_in_paise = int(round(amount * 100))
        
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f"receipt_{appointment_id}",
            "notes": {
                "appointment_id": appointment_id,
                "patient_id": appointment.patient_id,
                "doctor_id": doctor_user_id,
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

        # 9. Store the Payment Order with status = CREATED
        doctor_amount, platform_fee = PaymentService.calculate_revenue_split(amount)
        now = utc_now()
        
        payment_create = PaymentCreate(
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            doctor_id=doctor_user_id,
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

        # 10. Update Appointment's payment status to CREATED
        from app.schemas.appointment import AppointmentUpdateSchema
        app_update = AppointmentUpdateSchema(payment_status=AppPaymentStatus.CREATED)
        await self.appointment_repository.update(appointment.id, app_update)
        appointment = await self.appointment_repository.get(appointment_id)

        # 11. Audit Event: PAYMENT_ORDER_CREATED or PAYMENT_RETRY_CREATED
        action_name = "PAYMENT_RETRY_CREATED" if is_retry else "PAYMENT_ORDER_CREATED"
        try:
            audit_schema = AuditLogCreateSchema(
                user_id=current_user_id,
                action=action_name,
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
            logger.exception(f"Failed to write audit log for {action_name}")

        return payment_record, appointment

    async def verify_payment(
        self,
        payload: dict,
        current_user_id: str,
    ) -> Tuple[PaymentInDB, AppointmentInDB, dict, dict]:
        """
        Verify payment using Razorpay signature validation.
        """
        razorpay_payment_id = payload.get("razorpay_payment_id")
        razorpay_order_id = payload.get("razorpay_order_id")
        razorpay_signature = payload.get("razorpay_signature")

        if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
            raise ValueError("Missing payment gateway verification payload parameters")

        # 1. Fetch payment record
        payment_record = await self.payment_repository.get_by_filter({"razorpay_order_id": razorpay_order_id})
        if not payment_record:
            raise ValueError("Payment record not found")

        # 2. Check patient authorization
        if payment_record.patient_id != current_user_id:
            raise PermissionError("Unauthorized patient access to payment verification")

        # 3. Prevent duplicate success: if already verified successfully, return response immediately
        if payment_record.payment_status == PaymentStatus.SUCCESS:
            appointment = await self.appointment_repository.get(payment_record.appointment_id)
            wallet = await self.doctor_wallet_repository.get_by_doctor_id(payment_record.doctor_id)
            
            wallet_summary = {
                "doctor_id": payment_record.doctor_id,
                "previous_available_balance": wallet.available_balance if wallet else 0.0,
                "new_available_balance": wallet.available_balance if wallet else 0.0,
                "previous_lifetime_earnings": wallet.total_earned if wallet else 0.0,
                "new_lifetime_earnings": wallet.total_earned if wallet else 0.0,
            }
            
            revenue_split = {
                "amount": payment_record.amount,
                "doctor_share": payment_record.doctor_amount,
                "platform_share": payment_record.platform_fee,
                "currency": payment_record.currency,
            }
            
            return payment_record, appointment, wallet_summary, revenue_split

        # Check if there is another successful payment for this appointment (Duplicate verify prevention)
        other_success = await self.payment_repository.get_many({
            "appointment_id": payment_record.appointment_id,
            "payment_status": {"$in": [PaymentStatus.SUCCESS, PaymentStatus.APPROVED, PaymentStatus.COMPLETED]},
            "_id": {"$ne": ObjectId(payment_record.id) if isinstance(payment_record.id, str) else payment_record.id}
        })
        if other_success:
            raise ValueError("Appointment has already been paid under a different order")

        # 4. Verify Signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            await asyncio.to_thread(
                self.razorpay_client.utility.verify_payment_signature,
                params_dict
            )
        except Exception as exc:
            # Transition payment record to FAILED
            await self.payment_repository.update(payment_record.id, PaymentUpdate(payment_status=PaymentStatus.FAILED))
            
            # Transition appointment payment status to FAILED
            from app.schemas.appointment import AppointmentUpdateSchema
            app_update = AppointmentUpdateSchema(payment_status=AppPaymentStatus.FAILED)
            await self.appointment_repository.update(payment_record.appointment_id, app_update)
            
            # Audit log: PAYMENT_FAILED
            try:
                audit_schema = AuditLogCreateSchema(
                    user_id=current_user_id,
                    action="PAYMENT_FAILED",
                    resource_type="payments",
                    resource_id=payment_record.id,
                    old_value={"payment_status": "created"},
                    new_value={"payment_status": "failed", "error": str(exc)}
                )
                await self.audit_log_service.create_log(audit_schema)
            except Exception:
                logger.exception("Failed to write PAYMENT_FAILED audit log")
                
            raise ValueError(f"Invalid payment signature: {str(exc)}")

        # 5. Fetch and validate appointment
        appointment = await self.appointment_repository.get(payment_record.appointment_id)
        if not appointment:
            raise ValueError("Appointment request not found")

        # 6. Reject if cancelled
        if appointment.status == AppointmentStatus.CANCELLED:
            raise ValueError("Cannot verify payment for a cancelled appointment")

        # Check if there were any previous failures/cancellations for this appointment (to log retry success)
        prior_failures = await self.payment_repository.get_many({
            "appointment_id": payment_record.appointment_id,
            "payment_status": {"$in": [PaymentStatus.FAILED, PaymentStatus.CANCELLED]}
        })
        is_retry_success = len(prior_failures) > 0

        # 7. Update payment status to SUCCESS
        now = utc_now()
        payment_update = PaymentUpdate(
            payment_status=PaymentStatus.SUCCESS,
            razorpay_payment_id=razorpay_payment_id,
            verified_at=now,
            gateway_response=payload,
        )
        updated_payment = await self.payment_repository.update(payment_record.id, payment_update)
        if not updated_payment:
            raise RuntimeError("Failed to update payment status")

        # 8. Update appointment payment_status = PAID
        from app.schemas.appointment import AppointmentUpdateSchema
        app_update = AppointmentUpdateSchema(payment_status=AppPaymentStatus.PAID)
        await self.appointment_repository.update(appointment.id, app_update)
        appointment = await self.appointment_repository.get(payment_record.appointment_id)

        # 9. Update Doctor Wallet
        doctor_user_id = payment_record.doctor_id
        wallet = await self.doctor_wallet_repository.get_by_doctor_id(doctor_user_id)
        
        prev_available = 0.0
        prev_earned = 0.0
        
        if not wallet:
            # Initialize wallet automatically
            from app.models.payment import DoctorWalletCreate
            now_w = utc_now()
            wallet_create = DoctorWalletCreate(
                doctor_id=doctor_user_id,
                total_earned=0.0,
                total_withdrawn=0.0,
                available_balance=0.0,
                pending_balance=0.0,
                last_payout_at=None,
            )
            doc_dict = wallet_create.model_dump()
            doc_dict["created_at"] = now_w
            doc_dict["updated_at"] = now_w
            result = await self.doctor_wallet_repository.collection.insert_one(doc_dict)
            created_wallet = await self.doctor_wallet_repository.collection.find_one({"_id": result.inserted_id})
            wallet = DoctorWalletInDB.from_mongo(created_wallet)
        
        prev_available = wallet.available_balance
        prev_earned = wallet.total_earned

        new_available = prev_available + payment_record.doctor_amount
        new_earned = prev_earned + payment_record.doctor_amount

        from app.models.payment import DoctorWalletUpdate
        wallet_update_data = DoctorWalletUpdate(
            available_balance=new_available,
            total_earned=new_earned
        )
        await self.doctor_wallet_repository.update(wallet.id, wallet_update_data)

        wallet_summary = {
            "doctor_id": doctor_user_id,
            "previous_available_balance": prev_available,
            "new_available_balance": new_available,
            "previous_lifetime_earnings": prev_earned,
            "new_lifetime_earnings": new_earned,
        }

        revenue_split = {
            "amount": payment_record.amount,
            "doctor_share": payment_record.doctor_amount,
            "platform_share": payment_record.platform_fee,
            "currency": payment_record.currency,
        }

        # 10. Audit Logs
        # PAYMENT_VERIFIED or PAYMENT_RETRY_SUCCESS
        success_action = "PAYMENT_RETRY_SUCCESS" if is_retry_success else "PAYMENT_VERIFIED"
        try:
            audit_schema = AuditLogCreateSchema(
                user_id=current_user_id,
                action=success_action,
                resource_type="payments",
                resource_id=payment_record.id,
                old_value={"payment_status": "created"},
                new_value={"payment_status": "success", "razorpay_payment_id": razorpay_payment_id}
            )
            await self.audit_log_service.create_log(audit_schema)
        except Exception:
            logger.exception(f"Failed to write {success_action} audit log")

        # WALLET_UPDATED
        try:
            audit_schema = AuditLogCreateSchema(
                user_id=current_user_id,
                action="WALLET_UPDATED",
                resource_type="doctor_wallets",
                resource_id=wallet.id,
                old_value={"available_balance": prev_available, "total_earned": prev_earned},
                new_value={"available_balance": new_available, "total_earned": new_earned}
            )
            await self.audit_log_service.create_log(audit_schema)
        except Exception:
            logger.exception("Failed to write WALLET_UPDATED audit log")

        # REVENUE_SPLIT_RECORDED
        try:
            audit_schema = AuditLogCreateSchema(
                user_id=current_user_id,
                action="REVENUE_SPLIT_RECORDED",
                resource_type="payments",
                resource_id=payment_record.id,
                old_value=None,
                new_value={"doctor_share": payment_record.doctor_amount, "platform_share": payment_record.platform_fee}
            )
            await self.audit_log_service.create_log(audit_schema)
        except Exception:
            logger.exception("Failed to write REVENUE_SPLIT_RECORDED audit log")

        # 11. Notifications
        # Patient notification
        try:
            from app.schemas.notification import NotificationCreateSchema
            from app.models.notification import NotificationType, NotificationPriority
            
            doctor_profile = await self.doctor_profile_repository.get(appointment.doctor_id)
            doctor_name = "Doctor"
            if doctor_profile:
                doctor_user = await self.user_repository.get(doctor_profile.user_id)
                if doctor_user:
                    doctor_name = doctor_user.full_name

            patient_notif = NotificationCreateSchema(
                user_id=payment_record.patient_id,
                notification_type=NotificationType.PAYMENT_SUCCESSFUL,
                title="Payment Successful",
                message=f"Your payment of INR {payment_record.amount:.2f} for the appointment with Dr. {doctor_name} was successful.",
                priority=NotificationPriority.HIGH,
                related_entity_type="payment",
                related_entity_id=payment_record.id,
            )
            await self.notification_service.create_notification(patient_notif)
        except Exception:
            logger.exception("Failed to send patient payment successful notification")

        # Doctor notification
        try:
            from app.schemas.notification import NotificationCreateSchema
            from app.models.notification import NotificationType, NotificationPriority
            
            patient_user = await self.user_repository.get(payment_record.patient_id)
            patient_name = "Patient"
            if patient_user:
                patient_name = patient_user.full_name

            doctor_notif = NotificationCreateSchema(
                user_id=doctor_user_id,
                notification_type=NotificationType.PAYMENT_SUCCESSFUL,
                title="Payment Received",
                message=f"Payment of INR {payment_record.amount:.2f} has been received for your appointment with {patient_name}.",
                priority=NotificationPriority.MEDIUM,
                related_entity_type="payment",
                related_entity_id=payment_record.id,
            )
            await self.notification_service.create_notification(doctor_notif)
        except Exception:
            logger.exception("Failed to send doctor payment received notification")

        return updated_payment, appointment, wallet_summary, revenue_split

    async def fail_payment(
        self,
        payment_id: str,
        current_user_id: str,
        error_details: Optional[dict] = None,
    ) -> PaymentInDB:
        """
        Marks a payment record as failed (e.g. checkout reported error).
        """
        payment = await self.payment_repository.get(payment_id)
        if not payment:
            raise ValueError("Payment record not found")
            
        if payment.patient_id != current_user_id:
            raise PermissionError("Unauthorized patient access to payment record")
            
        if payment.payment_status in (PaymentStatus.SUCCESS, PaymentStatus.APPROVED, PaymentStatus.COMPLETED):
            raise ValueError("Cannot fail a payment that is already successful")
            
        now = utc_now()
        payment_update = PaymentUpdate(
            payment_status=PaymentStatus.FAILED,
            gateway_response=error_details,
            verified_at=now,
        )
        updated_payment = await self.payment_repository.update(payment_id, payment_update)
        if not updated_payment:
            raise RuntimeError("Failed to update payment status")
            
        # Update appointment payment status
        from app.schemas.appointment import AppointmentUpdateSchema
        app_update = AppointmentUpdateSchema(payment_status=AppPaymentStatus.FAILED)
        await self.appointment_repository.update(payment.appointment_id, app_update)
        
        # Audit Log: PAYMENT_FAILED
        try:
            audit_schema = AuditLogCreateSchema(
                user_id=current_user_id,
                action="PAYMENT_FAILED",
                resource_type="payments",
                resource_id=payment_id,
                old_value={"payment_status": payment.payment_status.value if hasattr(payment.payment_status, "value") else payment.payment_status},
                new_value={"payment_status": "failed", "error_details": error_details}
            )
            await self.audit_log_service.create_log(audit_schema)
        except Exception:
            logger.exception("Failed to write audit log for payment failure")
            
        return updated_payment

    async def cancel_payment(
        self,
        payment_id: str,
        current_user_id: str,
    ) -> PaymentInDB:
        """
        Marks a payment record as cancelled (e.g. user dismissed checkout modal).
        """
        payment = await self.payment_repository.get(payment_id)
        if not payment:
            raise ValueError("Payment record not found")
            
        if payment.patient_id != current_user_id:
            raise PermissionError("Unauthorized patient access to payment record")
            
        if payment.payment_status in (PaymentStatus.SUCCESS, PaymentStatus.APPROVED, PaymentStatus.COMPLETED):
            raise ValueError("Cannot cancel a payment that is already successful")
            
        now = utc_now()
        payment_update = PaymentUpdate(
            payment_status=PaymentStatus.CANCELLED,
            verified_at=now,
        )
        updated_payment = await self.payment_repository.update(payment_id, payment_update)
        if not updated_payment:
            raise RuntimeError("Failed to update payment status")
            
        # Update appointment payment status
        from app.schemas.appointment import AppointmentUpdateSchema
        app_update = AppointmentUpdateSchema(payment_status=AppPaymentStatus.CANCELLED)
        await self.appointment_repository.update(payment.appointment_id, app_update)
        
        # Audit Log: PAYMENT_CANCELLED
        try:
            audit_schema = AuditLogCreateSchema(
                user_id=current_user_id,
                action="PAYMENT_CANCELLED",
                resource_type="payments",
                resource_id=payment_id,
                old_value={"payment_status": payment.payment_status.value if hasattr(payment.payment_status, "value") else payment.payment_status},
                new_value={"payment_status": "cancelled"}
            )
            await self.audit_log_service.create_log(audit_schema)
        except Exception:
            logger.exception("Failed to write audit log for payment cancellation")
            
        return updated_payment
