"""
Nura - Doctor Earnings Service
Aggregates financial statistics, monthly earning reports, and transaction logs.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict
from bson import ObjectId

from app.repositories.doctor_wallet_repository import DoctorWalletRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.user_repository import UserRepository
from app.models.payment import PaymentStatus, DoctorWalletInDB, PaymentInDB
from app.schemas.payment import (
    DoctorEarningsResponse,
    MonthlyEarningsItem,
    RevenueTrendItem,
    DoctorWalletDetailsResponse,
    DoctorWalletResponse,
    PaymentResponse,
    DoctorTransactionItem,
    DoctorTransactionsResponse
)


class DoctorEarningsService:
    """Service layer for doctor financial metrics aggregation"""

    def __init__(
        self,
        doctor_wallet_repository: DoctorWalletRepository,
        payment_repository: PaymentRepository,
        appointment_repository: AppointmentRepository,
        user_repository: UserRepository
    ):
        self.doctor_wallet_repository = doctor_wallet_repository
        self.payment_repository = payment_repository
        self.appointment_repository = appointment_repository
        self.user_repository = user_repository

    async def get_earnings_summary(
        self,
        doctor_user_id: str,
        doctor_profile_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        skip: int = 0,
        sort_by: Optional[str] = None,
    ) -> DoctorEarningsResponse:
        """Aggregate doctor share, platform fees, monthly statistics, and daily revenue trends"""
        
        # 1. Fetch doctor wallet details
        wallet = await self.doctor_wallet_repository.get_by_doctor_id(doctor_user_id)
        if not wallet:
            available_balance = 0.0
            pending_balance = 0.0
            lifetime_earnings = 0.0
        else:
            available_balance = wallet.available_balance
            pending_balance = wallet.pending_balance
            lifetime_earnings = wallet.total_earned

        # 2. Build payment base query for statistics
        query = {
            "doctor_id": doctor_user_id,
            "payment_status": {"$in": [PaymentStatus.APPROVED.value, PaymentStatus.COMPLETED.value]}
        }

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

        # Fetch all successful payments matching query
        cursor = self.payment_repository.collection.find(query)
        all_payments = [PaymentInDB.from_mongo(doc) for doc in await cursor.to_list(length=10000)]

        # Calculate revenue shares
        platform_revenue_share = sum(p.platform_fee for p in all_payments)
        doctor_revenue_share = sum(p.doctor_amount for p in all_payments)

        # 3. Retrieve consultations counts from appointments matching profile ID
        total_consultations = await self.appointment_repository.collection.count_documents({
            "doctor_id": doctor_profile_id
        })
        completed_consultations = await self.appointment_repository.collection.count_documents({
            "doctor_id": doctor_profile_id,
            "status": "completed"
        })

        # Calculate average fee based on completed appointments
        completed_appts_cursor = self.appointment_repository.collection.find({
            "doctor_id": doctor_profile_id,
            "status": "completed"
        })
        completed_appts = [doc for doc in await completed_appts_cursor.to_list(length=10000)]
        if completed_appts:
            average_consultation_fee = sum(doc.get("consultation_fee", 0.0) for doc in completed_appts) / len(completed_appts)
        else:
            average_consultation_fee = 0.0

        # 4. Group by Month (Monthly Earnings Summary)
        monthly_map: Dict[str, float] = {}
        for p in all_payments:
            month_key = p.created_at.strftime("%Y-%m")
            monthly_map[month_key] = monthly_map.get(month_key, 0.0) + p.doctor_amount

        monthly_earnings_summary = [
            MonthlyEarningsItem(month=k, amount=round(v, 2))
            for k, v in sorted(monthly_map.items())
        ]

        # 5. Group by Day (Revenue Trend)
        daily_map: Dict[str, float] = {}
        for p in all_payments:
            date_key = p.created_at.strftime("%Y-%m-%d")
            daily_map[date_key] = daily_map.get(date_key, 0.0) + p.doctor_amount

        revenue_trend = [
            RevenueTrendItem(date=k, amount=round(v, 2))
            for k, v in sorted(daily_map.items())
        ]

        # 6. Recent payments paginated
        sort_field = "created_at"
        sort_direction = -1
        if sort_by == "amount":
            sort_field = "amount"
            sort_direction = 1
        elif sort_by == "-amount":
            sort_field = "amount"
            sort_direction = -1
        elif sort_by == "created_at":
            sort_field = "created_at"
            sort_direction = 1

        recent_cursor = self.payment_repository.collection.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
        recent_payments = [PaymentInDB.from_mongo(doc) for doc in await recent_cursor.to_list(length=limit + 5)]
        recent_transactions = [self.payment_repository.to_response(p) for p in recent_payments]

        return DoctorEarningsResponse(
            available_balance=round(available_balance, 2),
            pending_balance=round(pending_balance, 2),
            lifetime_earnings=round(lifetime_earnings, 2),
            platform_revenue_share=round(platform_revenue_share, 2),
            doctor_revenue_share=round(doctor_revenue_share, 2),
            total_consultations=total_consultations,
            total_completed_consultations=completed_consultations,
            average_consultation_fee=round(average_consultation_fee, 2),
            monthly_earnings_summary=monthly_earnings_summary,
            recent_transactions=recent_transactions,
            revenue_trend=revenue_trend,
        )

    async def get_wallet_details(self, doctor_user_id: str) -> DoctorWalletDetailsResponse:
        """Fetch doctor's wallet balances. Fallback to default zero if missing."""
        wallet = await self.doctor_wallet_repository.get_by_doctor_id(doctor_user_id)
        if not wallet:
            wallet = DoctorWalletInDB(
                id="default_wallet_id",
                doctor_id=doctor_user_id,
                total_earned=0.0,
                total_withdrawn=0.0,
                available_balance=0.0,
                pending_balance=0.0,
                last_payout_at=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        
        wallet_resp = DoctorWalletResponse(
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

        return DoctorWalletDetailsResponse(
            wallet_details=wallet_resp,
            pending_amount=round(wallet.pending_balance, 2),
            available_amount=round(wallet.available_balance, 2),
            lifetime_earnings=round(wallet.total_earned, 2),
            total_withdrawn=round(wallet.total_withdrawn, 2)
        )

    async def get_transactions(
        self,
        doctor_user_id: str,
        limit: int = 100,
        skip: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
    ) -> DoctorTransactionsResponse:
        """Fetch doctor's payment transactions applying range, status, and page limits"""
        query = {"doctor_id": doctor_user_id}

        if status:
            query["payment_status"] = status

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

        transactions_list = []
        for p in payments:
            patient_name = "Patient"
            if p.patient_id and ObjectId.is_valid(p.patient_id):
                patient_user = await self.user_repository.get(p.patient_id)
                if patient_user:
                    patient_name = patient_user.full_name

            transactions_list.append(
                DoctorTransactionItem(
                    id=p.id,
                    appointment_id=p.appointment_id,
                    patient_id=p.patient_id,
                    patient_name=patient_name,
                    consultation_fee=p.amount,
                    doctor_share=p.doctor_amount,
                    platform_share=p.platform_fee,
                    status=p.payment_status.value if hasattr(p.payment_status, 'value') else p.payment_status,
                    created_at=p.created_at
                )
            )

        return DoctorTransactionsResponse(
            transactions=transactions_list,
            total=total
        )
