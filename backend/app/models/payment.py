"""
Nura - Payment and Wallet Models
MongoDB models for payments and doctor_wallets collections
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class PaymentStatus(str, Enum):
    """Payment states for escrow and lifecycle management"""
    CREATED = "created"
    SUCCESS = "success"
    PENDING = "pending"
    HELD = "held"
    APPROVED = "approved"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    """Supported payment checkout methods"""
    RAZORPAY = "razorpay"
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"


# ---------------------------------------------------------------------------
# Payment Models
# ---------------------------------------------------------------------------

class PaymentBase(BaseModel):
    """Base fields shared by payment models"""
    model_config = ConfigDict(populate_by_name=True)

    appointment_id: str = Field(..., description="Reference to the appointment ID")
    patient_id: str = Field(..., description="Reference to the patient user ID")
    doctor_id: str = Field(..., description="Reference to the doctor profile user ID")
    amount: float = Field(..., ge=0.0, description="Total amount paid")
    platform_fee: float = Field(..., ge=0.0, description="Platform's 15% share")
    doctor_amount: float = Field(..., ge=0.0, description="Doctor's 85% share")
    currency: str = Field(default="INR", description="Three-letter ISO currency code")
    payment_method: PaymentMethod = Field(..., description="Method used for checkout")
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Status of the payment transaction")
    transaction_reference: Optional[str] = Field(None, description="Payment gateway transaction ID / reference")
    escrow_held: bool = Field(default=False, description="Whether the payment is currently held in escrow")

    # Future Payment Preparation (Task 8 Design Fields)
    razorpay_order_id: Optional[str] = Field(None, description="Proactive preparation for Razorpay Order ID link")
    razorpay_payment_id: Optional[str] = Field(None, description="Razorpay payment ID")
    verified_at: Optional[datetime] = Field(None, description="Payment verification timestamp")
    gateway_response: Optional[Dict[str, Any]] = Field(None, description="Gateway raw callback response JSON")
    escrow_released_at: Optional[datetime] = Field(None, description="Proactive preparation for escrow lifecycle release")
    escrow_released_by: Optional[str] = Field(None, description="Proactive preparation for escrow lifecycle authority")
    refunded_at: Optional[datetime] = Field(None, description="Proactive preparation for refund logs")
    refund_reason: Optional[str] = Field(None, description="Proactive preparation for refund details")
    analytics_metadata: Dict[str, Any] = Field(default_factory=dict, description="Proactive preparation for earnings analytics logs")


class PaymentCreate(PaymentBase):
    """Model used to create a new payment record"""
    pass


class PaymentUpdate(BaseModel):
    """Model used to update an existing payment record"""
    payment_status: Optional[PaymentStatus] = None
    transaction_reference: Optional[str] = None
    escrow_held: Optional[bool] = None
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    verified_at: Optional[datetime] = None
    gateway_response: Optional[Dict[str, Any]] = None
    escrow_released_at: Optional[datetime] = None
    escrow_released_by: Optional[str] = None
    refunded_at: Optional[datetime] = None
    refund_reason: Optional[str] = None
    analytics_metadata: Optional[Dict[str, Any]] = None


class PaymentInDB(PaymentBase):
    """Payment as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Transaction creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "PaymentInDB":
        """Create PaymentInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("appointment_id", "patient_id", "doctor_id", "escrow_released_by"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)


# ---------------------------------------------------------------------------
# Doctor Wallet Models
# ---------------------------------------------------------------------------

class DoctorWalletBase(BaseModel):
    """Base fields shared by doctor wallet models"""
    model_config = ConfigDict(populate_by_name=True)

    doctor_id: str = Field(..., description="Reference to the doctor user / profile ID")
    total_earned: float = Field(default=0.0, ge=0.0, description="Lifetime earned amount before payout")
    total_withdrawn: float = Field(default=0.0, ge=0.0, description="Lifetime withdrawn amount")
    available_balance: float = Field(default=0.0, ge=0.0, description="Withdrawable balance in wallet")
    pending_balance: float = Field(default=0.0, ge=0.0, description="Balance held in escrow / pending clearance")
    last_payout_at: Optional[datetime] = Field(None, description="Timestamp of the last payout execution")


class DoctorWalletCreate(DoctorWalletBase):
    """Model used to initialize a new doctor wallet"""
    pass


class DoctorWalletUpdate(BaseModel):
    """Model used to update wallet balances"""
    total_earned: Optional[float] = Field(None, ge=0.0)
    total_withdrawn: Optional[float] = Field(None, ge=0.0)
    available_balance: Optional[float] = Field(None, ge=0.0)
    pending_balance: Optional[float] = Field(None, ge=0.0)
    last_payout_at: Optional[datetime] = None


class DoctorWalletInDB(DoctorWalletBase):
    """Doctor wallet as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Wallet creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "DoctorWalletInDB":
        """Create DoctorWalletInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        if "doctor_id" in doc and doc["doctor_id"] is not None and not isinstance(doc["doctor_id"], str):
            doc["doctor_id"] = str(doc["doctor_id"])
        return cls(**doc)
