"""
Nura - Payment and Wallet Schemas
Pydantic v2 schemas for payment and wallet API requests and responses
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.payment import (
    PaymentStatus,
    PaymentMethod,
)


# ---------------------------------------------------------------------------
# Payment Schemas
# ---------------------------------------------------------------------------

class PaymentCreateSchema(BaseModel):
    """Request schema for creating a new payment record"""
    appointment_id: str = Field(..., description="Reference to the appointment ID")
    patient_id: str = Field(..., description="Reference to the patient user ID")
    doctor_id: str = Field(..., description="Reference to the doctor user ID")
    amount: float = Field(..., ge=0.0, description="Total payment amount")
    currency: str = Field(default="INR", description="Three-letter ISO currency code")
    payment_method: PaymentMethod = Field(..., description="Checkout method used")
    transaction_reference: Optional[str] = Field(None, description="Optional payment gateway reference ID")
    escrow_held: bool = Field(default=False, description="Whether escrow is active on this payment")

    # Future Payment Preparation (Task 8 Design Fields)
    razorpay_order_id: Optional[str] = Field(None, description="Razorpay order link ID")
    analytics_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Flexible analytics dictionary")


class PaymentUpdateSchema(BaseModel):
    """Request schema for updating a payment record"""
    payment_status: Optional[PaymentStatus] = None
    transaction_reference: Optional[str] = None
    escrow_held: Optional[bool] = None
    razorpay_order_id: Optional[str] = None
    escrow_released_at: Optional[datetime] = None
    escrow_released_by: Optional[str] = None
    refunded_at: Optional[datetime] = None
    refund_reason: Optional[str] = None
    analytics_metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    """Response schema for a payment transaction"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Payment record ID")
    appointment_id: str = Field(..., description="Appointment ID")
    patient_id: str = Field(..., description="Patient user ID")
    doctor_id: str = Field(..., description="Doctor user ID")
    amount: float = Field(..., description="Total payment amount")
    platform_fee: float = Field(..., description="Platform's 15% fee")
    doctor_amount: float = Field(..., description="Doctor's 85% amount")
    currency: str = Field(..., description="Payment currency code")
    payment_method: PaymentMethod = Field(..., description="Checkout method")
    payment_status: PaymentStatus = Field(..., description="Transaction status")
    transaction_reference: Optional[str] = Field(None, description="Gateway transaction reference")
    escrow_held: bool = Field(..., description="Escrow status")

    # Future Payment Preparation (Task 8 Design Fields)
    razorpay_order_id: Optional[str] = Field(None)
    escrow_released_at: Optional[datetime] = Field(None)
    escrow_released_by: Optional[str] = Field(None)
    refunded_at: Optional[datetime] = Field(None)
    refund_reason: Optional[str] = Field(None)
    analytics_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(..., description="Payment timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Doctor Wallet Schemas
# ---------------------------------------------------------------------------

class DoctorWalletCreateSchema(BaseModel):
    """Request schema for initializing a doctor wallet"""
    doctor_id: str = Field(..., description="Reference to the doctor user ID")


class DoctorWalletUpdateSchema(BaseModel):
    """Request schema for updating wallet balances"""
    total_earned: Optional[float] = Field(None, ge=0.0)
    total_withdrawn: Optional[float] = Field(None, ge=0.0)
    available_balance: Optional[float] = Field(None, ge=0.0)
    pending_balance: Optional[float] = Field(None, ge=0.0)
    last_payout_at: Optional[datetime] = None


class DoctorWalletResponse(BaseModel):
    """Response schema for a doctor wallet"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Wallet record ID")
    doctor_id: str = Field(..., description="Doctor user ID")
    total_earned: float = Field(..., description="Lifetime total earnings")
    total_withdrawn: float = Field(..., description="Lifetime total withdrawals")
    available_balance: float = Field(..., description="Available withdrawable balance")
    pending_balance: float = Field(..., description="Pending clearance balance")
    last_payout_at: Optional[datetime] = Field(None, description="Last payout timestamp")
    created_at: datetime = Field(..., description="Wallet creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Doctor Earnings & Transactions Dashboards Schemas (Sprint 8)
# ---------------------------------------------------------------------------

class MonthlyEarningsItem(BaseModel):
    """Monthly aggregated earnings for a doctor"""
    month: str = Field(..., description="Calendar month in YYYY-MM format")
    amount: float = Field(..., description="Doctor share amount earned in this month")


class RevenueTrendItem(BaseModel):
    """Daily revenue trend tracking"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    amount: float = Field(..., description="Doctor share amount earned on this date")


class DoctorEarningsResponse(BaseModel):
    """Full financial breakdown response for a doctor profile"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    available_balance: float = Field(..., description="Current withdrawable balance")
    pending_balance: float = Field(..., description="Balance currently held in escrow")
    lifetime_earnings: float = Field(..., description="Total lifetime earned doctor share")
    platform_revenue_share: float = Field(..., description="Total 15% revenue share taken by platform")
    doctor_revenue_share: float = Field(..., description="Total 85% revenue share received by doctor")
    total_consultations: int = Field(..., description="Total appointments scheduled for the doctor")
    total_completed_consultations: int = Field(..., description="Total completed consultations")
    average_consultation_fee: float = Field(..., description="Average fee charged per completed consultation")
    monthly_earnings_summary: List[MonthlyEarningsItem] = Field(default_factory=list, description="Earnings grouped by month")
    recent_transactions: List[PaymentResponse] = Field(default_factory=list, description="Recent payment transaction logs")
    revenue_trend: List[RevenueTrendItem] = Field(default_factory=list, description="Daily earnings tracking points")


class DoctorWalletDetailsResponse(BaseModel):
    """Detailed wallet balances status for the doctor profile"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    wallet_details: DoctorWalletResponse = Field(..., description="Base wallet metrics model")
    pending_amount: float = Field(..., description="Amount currently held pending clearance")
    available_amount: float = Field(..., description="Withdrawable cash amount available")
    lifetime_earnings: float = Field(..., description="Total lifetime earned amount")
    total_withdrawn: float = Field(..., description="Total payout withdrawn amount")


class DoctorTransactionItem(BaseModel):
    """Single payment transaction log entry with aggregated patient details"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Transaction/Payment ID")
    appointment_id: str = Field(..., description="Reference to appointment ID")
    patient_id: str = Field(..., description="Patient user ID")
    patient_name: str = Field(..., description="Patient full name")
    consultation_fee: float = Field(..., description="Total amount paid")
    doctor_share: float = Field(..., description="Doctor's 85% share amount")
    platform_share: float = Field(..., description="Platform's 15% fee amount")
    status: str = Field(..., description="Payment/ Escrow clearance status")
    created_at: datetime = Field(..., description="Transaction timestamp")


class DoctorTransactionsResponse(BaseModel):
    """Paginated list of transactions logs"""
    transactions: List[DoctorTransactionItem] = Field(..., description="Transactions list page")
    total: int = Field(..., description="Total transaction records matching filters")

