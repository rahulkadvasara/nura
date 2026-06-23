"""
Nura - Appointment Request System Router
API endpoints for patients to request, retrieve, and cancel appointments
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import UserInDB, UserRole
from app.schemas.auth import SuccessResponse
from app.schemas.appointment import AppointmentCreateSchema, AppointmentResponse
from app.core.dependencies import get_current_user, get_appointment_service
from app.services.appointment_service import AppointmentService

logger = logging.getLogger(__name__)

router = APIRouter()


def require_exact_patient(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Enforce that the logged-in user has exactly the PATIENT role."""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients are permitted to access this resource",
        )
    return current_user


@router.post(
    "",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Appointment Request",
    description="Allows a patient to request a consultation using an available doctor slot.",
)
async def create_appointment(
    schema: AppointmentCreateSchema,
    current_user: UserInDB = Depends(require_exact_patient),
    service: AppointmentService = Depends(get_appointment_service),
) -> SuccessResponse:
    try:
        created = await service.create_appointment(current_user.id, schema)
        return SuccessResponse(
            success=True,
            message="Appointment request created successfully",
            data=service.to_response(created).model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to create appointment request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create appointment request",
        ) from exc


@router.get(
    "/my",
    response_model=SuccessResponse,
    summary="Get My Appointments",
    description="Retrieves the appointment request history for the logged-in patient.",
)
async def get_my_appointments(
    current_user: UserInDB = Depends(require_exact_patient),
    service: AppointmentService = Depends(get_appointment_service),
) -> SuccessResponse:
    try:
        history = await service.list_patient_appointments_history(current_user.id)
        return SuccessResponse(
            success=True,
            message="Appointments retrieved successfully",
            data={"appointments": history},
        )
    except Exception as exc:
        logger.exception("Failed to retrieve patient appointments")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve appointments",
        ) from exc


@router.get(
    "/{appointment_id}",
    response_model=SuccessResponse,
    summary="Get Appointment Details",
    description="Retrieves detailed information of a specific appointment request.",
)
async def get_appointment_details(
    appointment_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    service: AppointmentService = Depends(get_appointment_service),
) -> SuccessResponse:
    try:
        appointment = await service.get_appointment_by_id(appointment_id)
        if not appointment or appointment.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment request not found",
            )
        return SuccessResponse(
            success=True,
            message="Appointment details retrieved successfully",
            data=service.to_response(appointment).model_dump(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve appointment details for %s", appointment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve appointment details",
        ) from exc


@router.delete(
    "/{appointment_id}",
    response_model=SuccessResponse,
    summary="Cancel Appointment Request",
    description="Allows a patient to cancel their own pending appointment request.",
)
async def cancel_appointment(
    appointment_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    service: AppointmentService = Depends(get_appointment_service),
) -> SuccessResponse:
    try:
        await service.cancel_patient_appointment(appointment_id, current_user.id)
        return SuccessResponse(
            success=True,
            message="Appointment request cancelled successfully",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to cancel appointment request %s", appointment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel appointment request",
        ) from exc
