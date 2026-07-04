"""
Nura - Payment Service
Business logic, validation, and revenue split calculations for payments
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from bson import ObjectId
import logging

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

logger = logging.getLogger(__name__)


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
        razorpay_payment_id=payment.razorpay_payment_id,
        verified_at=payment.verified_at,
        gateway_response=payment.gateway_response,
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
        audit_log_service: Optional[Any] = None,
    ):
        super().__init__()
        self.payment_repository = payment_repository
        self.appointment_repository = appointment_repository
        self.user_repository = user_repository
        self.doctor_profile_repository = doctor_profile_repository
        self.audit_log_service = audit_log_service


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

    async def list_patient_payment_history(
        self,
        patient_id: str,
        search: Optional[str] = None,
        status: Optional[str] = None,
        doctor_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> Tuple[List[Any], int]:
        """Fetch patient's payment logs with pagination, search, status, and range filters"""
        query = {"patient_id": patient_id}

        if status:
            query["payment_status"] = status

        if doctor_id:
            query["doctor_id"] = doctor_id

        if search:
            # Query users collection for doctor matches
            user_cursor = self.user_repository.collection.find({
                "role": "doctor",
                "full_name": {"$regex": search, "$options": "i"}
            })
            matching_doctor_ids = [str(u["_id"]) for u in await user_cursor.to_list(length=500)]
            if not matching_doctor_ids:
                return [], 0
            query["doctor_id"] = {"$in": matching_doctor_ids}

        if start_date or end_date:
            date_query = {}
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
                    date_query["$gte"] = start_dt
                except ValueError:
                    pass
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
                    date_query["$lte"] = end_dt
                except ValueError:
                    pass
            if date_query:
                query["created_at"] = date_query

        total = await self.payment_repository.collection.count_documents(query)
        cursor = self.payment_repository.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        payments = [PaymentInDB.from_mongo(doc) for doc in await cursor.to_list(length=limit + 5)]

        payments_history = []
        for p in payments:
            appointment_data = {}
            appointment = await self.appointment_repository.get(p.appointment_id)
            if appointment:
                appointment_data = {
                    "id": appointment.id,
                    "slot_date": appointment.slot_date,
                    "slot_time": appointment.slot_time,
                    "status": appointment.status.value if hasattr(appointment.status, "value") else appointment.status,
                    "reason": appointment.reason,
                }

            doctor_data = {"id": p.doctor_id, "full_name": "Doctor", "specialization": "Specialist", "email": ""}
            doctor_user = await self.user_repository.get(p.doctor_id)
            if doctor_user:
                doctor_data["full_name"] = doctor_user.full_name
                doctor_data["email"] = doctor_user.email
                
                profile_doc = await self.payment_repository.collection.database["doctor_profiles"].find_one({"user_id": p.doctor_id})
                if profile_doc:
                    doctor_data["specialization"] = profile_doc.get("specialization", "Specialist")

            receipt_info = {
                "razorpay_order_id": p.razorpay_order_id,
                "razorpay_payment_id": p.razorpay_payment_id,
                "payment_method": p.payment_method.value if hasattr(p.payment_method, "value") else p.payment_method,
                "transaction_reference": p.transaction_reference,
                "doctor_share": p.doctor_amount,
                "platform_fee": p.platform_fee,
            }

            from app.schemas.payment import PatientPaymentHistoryItemSchema
            payments_history.append(
                PatientPaymentHistoryItemSchema(
                    payment_id=p.id,
                    appointment=appointment_data,
                    doctor=doctor_data,
                    amount=p.amount,
                    status=p.payment_status.value if hasattr(p.payment_status, "value") else p.payment_status,
                    created_date=p.created_at,
                    paid_date=p.verified_at,
                    receipt_information=receipt_info,
                )
            )

        return payments_history, total

    async def list_payments_for_admin(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        doctor_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> Tuple[List[Any], int]:
        """Fetch all platform payments matching filters for the admin view"""
        query = {}

        if status:
            query["payment_status"] = status

        if doctor_id:
            query["doctor_id"] = doctor_id

        if patient_id:
            query["patient_id"] = patient_id

        if search:
            user_cursor = self.user_repository.collection.find({
                "$or": [
                    {"full_name": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}}
                ]
            })
            matching_ids = [str(u["_id"]) for u in await user_cursor.to_list(length=1000)]
            if not matching_ids:
                return [], 0
            query["$or"] = [
                {"patient_id": {"$in": matching_ids}},
                {"doctor_id": {"$in": matching_ids}}
            ]

        if start_date or end_date:
            date_query = {}
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
                    date_query["$gte"] = start_dt
                except ValueError:
                    pass
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
                    date_query["$lte"] = end_dt
                except ValueError:
                    pass
            if date_query:
                query["created_at"] = date_query

        total = await self.payment_repository.collection.count_documents(query)
        cursor = self.payment_repository.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        payments = [PaymentInDB.from_mongo(doc) for doc in await cursor.to_list(length=limit + 5)]

        admin_payments = []
        for p in payments:
            patient_data = {"id": p.patient_id, "full_name": "Patient", "email": ""}
            patient_user = await self.user_repository.get(p.patient_id)
            if patient_user:
                patient_data["full_name"] = patient_user.full_name
                patient_data["email"] = patient_user.email

            doctor_data = {"id": p.doctor_id, "full_name": "Doctor", "email": "", "specialization": "Specialist"}
            doctor_user = await self.user_repository.get(p.doctor_id)
            if doctor_user:
                doctor_data["full_name"] = doctor_user.full_name
                doctor_data["email"] = doctor_user.email
                profile_doc = await self.payment_repository.collection.database["doctor_profiles"].find_one({"user_id": p.doctor_id})
                if profile_doc:
                    doctor_data["specialization"] = profile_doc.get("specialization", "Specialist")

            from app.schemas.payment import AdminPaymentListItemSchema
            admin_payments.append(
                AdminPaymentListItemSchema(
                    payment_id=p.id,
                    appointment_id=p.appointment_id,
                    patient=patient_data,
                    doctor=doctor_data,
                    amount=p.amount,
                    doctor_share=p.doctor_amount,
                    platform_share=p.platform_fee,
                    payment_status=p.payment_status.value if hasattr(p.payment_status, "value") else p.payment_status,
                    created_at=p.created_at,
                    verified_at=p.verified_at,
                )
            )

        return admin_payments, total

    async def get_admin_payments_summary(self) -> Any:
        """Calculate global dashboard transaction numbers and daily/monthly aggregates"""
        success_statuses = ["success", "paid", "completed", "approved", "held"]
        success_query = {"payment_status": {"$in": success_statuses}}
        
        cursor = self.payment_repository.collection.find(success_query)
        successful_payments = [PaymentInDB.from_mongo(doc) for doc in await cursor.to_list(length=100000)]

        total_revenue = sum(p.amount for p in successful_payments)
        doctor_payouts = sum(p.doctor_amount for p in successful_payments)
        platform_earnings = sum(p.platform_fee for p in successful_payments)
        success_count = len(successful_payments)

        failed_count = await self.payment_repository.collection.count_documents({"payment_status": "failed"})
        pending_count = await self.payment_repository.collection.count_documents({
            "payment_status": {"$in": ["created", "pending"]}
        })
        total_transactions = await self.payment_repository.collection.count_documents({})

        # Compute refunded payments/revenue
        refunded_query = {"payment_status": "refunded"}
        refunded_payments_cursor = self.payment_repository.collection.find(refunded_query)
        refunded_payments_list = [PaymentInDB.from_mongo(doc) for doc in await refunded_payments_cursor.to_list(length=100000)]
        refunded_count = len(refunded_payments_list)
        refunded_revenue = sum(p.amount for p in refunded_payments_list)

        # Compute failed revenue
        failed_query = {"payment_status": "failed"}
        failed_payments_cursor = self.payment_repository.collection.find(failed_query)
        failed_payments_list = [PaymentInDB.from_mongo(doc) for doc in await failed_payments_cursor.to_list(length=100000)]
        failed_revenue = sum(p.amount for p in failed_payments_list)

        # Compute pending payouts (created, pending, held payments)
        pending_query = {"payment_status": {"$in": ["created", "pending", "held"]}}
        pending_payments_cursor = self.payment_repository.collection.find(pending_query)
        pending_payments_list = [PaymentInDB.from_mongo(doc) for doc in await pending_payments_cursor.to_list(length=100000)]
        pending_payouts = sum(p.doctor_amount for p in pending_payments_list)

        average_fee = total_revenue / success_count if success_count > 0 else 0.0

        monthly_map = {}
        for p in successful_payments:
            month = p.created_at.strftime("%Y-%m")
            if month not in monthly_map:
                monthly_map[month] = {"amount": 0.0, "doctor_share": 0.0, "platform_share": 0.0}
            monthly_map[month]["amount"] += p.amount
            monthly_map[month]["doctor_share"] += p.doctor_amount
            monthly_map[month]["platform_share"] += p.platform_fee

        from app.schemas.payment import MonthlyRevenueItem
        monthly_revenue = [
            MonthlyRevenueItem(
                month=m,
                amount=round(v["amount"], 2),
                doctor_share=round(v["doctor_share"], 2),
                platform_share=round(v["platform_share"], 2),
            )
            for m, v in sorted(monthly_map.items())
        ]

        daily_map = {}
        for p in successful_payments:
            date = p.created_at.strftime("%Y-%m-%d")
            if date not in daily_map:
                daily_map[date] = {"amount": 0.0, "doctor_share": 0.0, "platform_share": 0.0}
            daily_map[date]["amount"] += p.amount
            daily_map[date]["doctor_share"] += p.doctor_amount
            daily_map[date]["platform_share"] += p.platform_fee

        from app.schemas.payment import DailyRevenueItem
        daily_revenue = [
            DailyRevenueItem(
                date=d,
                amount=round(v["amount"], 2),
                doctor_share=round(v["doctor_share"], 2),
                platform_share=round(v["platform_share"], 2),
            )
            for d, v in sorted(daily_map.items())
        ]

        from app.schemas.payment import AdminRevenueSummaryResponse
        return AdminRevenueSummaryResponse(
            total_revenue=round(total_revenue, 2),
            doctor_payouts=round(doctor_payouts, 2),
            platform_earnings=round(platform_earnings, 2),
            successful_payments=success_count,
            failed_payments=failed_count,
            pending_payments=pending_count,
            average_consultation_fee=round(average_fee, 2),
            total_transactions=total_transactions,
            monthly_revenue=monthly_revenue,
            daily_revenue=daily_revenue,
            pending_payouts=round(pending_payouts, 2),
            refunded_payments=refunded_count,
            refunded_revenue=round(refunded_revenue, 2),
            failed_revenue=round(failed_revenue, 2),
        )


    async def get_payment_detail_for_admin(self, payment_id: str, admin_user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch details of a single payment for administrator view, and audit-log the access"""
        payment = await self.payment_repository.get(payment_id)
        if not payment:
            return None

        patient_data = {"id": payment.patient_id, "full_name": "Patient", "email": ""}
        patient_user = await self.user_repository.get(payment.patient_id)
        if patient_user:
            patient_data["full_name"] = patient_user.full_name
            patient_data["email"] = patient_user.email

        doctor_data = {"id": payment.doctor_id, "full_name": "Doctor", "email": "", "specialization": "Specialist"}
        doctor_user = await self.user_repository.get(payment.doctor_id)
        if doctor_user:
            doctor_data["full_name"] = doctor_user.full_name
            doctor_data["email"] = doctor_user.email
            profile_doc = await self.payment_repository.collection.database["doctor_profiles"].find_one({"user_id": payment.doctor_id})
            if profile_doc:
                doctor_data["specialization"] = profile_doc.get("specialization", "Specialist")

        appointment_data = {}
        appointment = await self.appointment_repository.get(payment.appointment_id)
        if appointment:
            appointment_data = {
                "id": appointment.id,
                "slot_date": appointment.slot_date,
                "slot_time": appointment.slot_time,
                "status": appointment.status.value if hasattr(appointment.status, "value") else appointment.status,
                "reason": appointment.reason,
                "consultation_fee": appointment.consultation_fee,
            }

        # Log audit log
        if self.audit_log_service:
            try:
                from app.schemas.observability import AuditLogCreateSchema
                audit_schema = AuditLogCreateSchema(
                    user_id=admin_user_id,
                    action="PAYMENT_VIEWED_ADMIN",
                    resource_type="payments",
                    resource_id=payment_id,
                    old_value=None,
                    new_value={
                        "payment_status": payment.payment_status.value if hasattr(payment.payment_status, "value") else payment.payment_status,
                        "amount": payment.amount,
                    }
                )
                await self.audit_log_service.create_log(audit_schema)
            except Exception:
                logger.exception("Failed to write PAYMENT_VIEWED_ADMIN audit log")

        return {
            "payment_id": payment.id,
            "appointment_id": payment.appointment_id,
            "appointment": appointment_data,
            "patient": patient_data,
            "doctor": doctor_data,
            "amount": payment.amount,
            "doctor_share": payment.doctor_amount,
            "platform_share": payment.platform_fee,
            "payment_status": payment.payment_status.value if hasattr(payment.payment_status, "value") else payment.payment_status,
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": payment.razorpay_payment_id,
            "gateway_response": payment.gateway_response,
            "created_at": payment.created_at,
            "verified_at": payment.verified_at,
        }

