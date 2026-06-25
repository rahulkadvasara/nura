"""
Nura - Payments Router
API endpoints for creating payment orders.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.models.user import UserInDB
from app.core.dependencies import (
    require_exact_patient,
    get_payment_gateway_service,
    get_appointment_service,
)
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
