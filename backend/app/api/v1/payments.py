"""
Nura - Payments Router
API endpoints for creating payment orders.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.models.user import UserInDB
from app.core.dependencies import (
    require_exact_patient,
    get_payment_gateway_service,
    get_appointment_service,
    get_payment_service,
)
from app.services.payment_service import PaymentService

from app.schemas.auth import SuccessResponse
from app.services.payment_gateway_service import PaymentGatewayService
from app.services.appointment_service import AppointmentService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class PaymentOrderRequest(BaseModel):
    appointment_id: str = Field(..., description="The ID of the appointment to pay for")


@router.post(
    "/order",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Razorpay Payment Order",
    description="Validates an appointment and creates a Razorpay payment order.",
)
async def create_payment_order(
    payload: PaymentOrderRequest,
    current_user: UserInDB = Depends(require_exact_patient),
    payment_gateway_service: PaymentGatewayService = Depends(get_payment_gateway_service),
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> SuccessResponse:
    try:
        payment, appointment = await payment_gateway_service.create_payment_order(
            appointment_id=payload.appointment_id,
            current_user_id=current_user.id,
        )
        
        response_data = {
            "razorpay_order_id": payment.razorpay_order_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "appointment": appointment_service.to_response(appointment).model_dump(),
        }
        
        return SuccessResponse(
            success=True,
            message="Payment order created successfully",
            data=response_data,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to create payment order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment order",
        ) from exc


class PaymentVerifyRequest(BaseModel):
    razorpay_payment_id: str = Field(..., description="The payment ID returned by Razorpay Checkout")
    razorpay_order_id: str = Field(..., description="The order ID returned by Razorpay Checkout")
    razorpay_signature: str = Field(..., description="The signature returned by Razorpay Checkout")


@router.post(
    "/verify",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Razorpay Payment Signature",
    description="Verifies a Razorpay payment signature, updates payment/appointment status, splits revenue, updates wallet, and notifies users.",
)
async def verify_payment(
    payload: PaymentVerifyRequest,
    current_user: UserInDB = Depends(require_exact_patient),
    payment_gateway_service: PaymentGatewayService = Depends(get_payment_gateway_service),
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> SuccessResponse:
    try:
        payment, appointment, wallet_summary, revenue_split = await payment_gateway_service.verify_payment(
            payload=payload.model_dump(),
            current_user_id=current_user.id,
        )
        
        response_data = {
            "payment": payment_gateway_service.payment_repository.to_response(payment).model_dump(),
            "appointment": appointment_service.to_response(appointment).model_dump(),
            "wallet_update_summary": wallet_summary,
            "revenue_split_summary": revenue_split,
        }
        
        return SuccessResponse(
            success=True,
            message="Payment verified successfully",
            data=response_data,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to verify payment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment",
        ) from exc


@router.get(
    "/history",
    response_model=SuccessResponse,
    summary="Get Patient Payment History",
    description="Retrieve paginated payment transactions history for the logged-in patient with filters.",
)
async def get_patient_payment_history(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    doctor_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user: UserInDB = Depends(require_exact_patient),
    payment_service: PaymentService = Depends(get_payment_service),
) -> SuccessResponse:
    try:
        payments, total = await payment_service.list_patient_payment_history(
            patient_id=current_user.id,
            search=search,
            status=status_filter,
            doctor_id=doctor_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            skip=skip,
        )
        return SuccessResponse(
            success=True,
            message="Patient payment history retrieved successfully",
            data={
                "payments": [item.model_dump() for item in payments],
                "total": total,
            }
        )
    except Exception as exc:
        logger.exception("Failed to retrieve patient payment history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient payment history",
        ) from exc

