"""
Nura - Payment and Wallet Schemas
Pydantic v2 schemas for payment and wallet API requests and responses
"""

from datetime import datetime
from typing import Any, Dict, Optional
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
