"""
Nura - Doctor Discovery & Slot Browsing Router
Endpoints for patients to search, filter, and view verified doctors and upcoming availability slots.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import UserInDB, UserRole
from app.schemas.auth import SuccessResponse
from app.schemas.doctor import DoctorDiscoveryResponse, DoctorAvailabilityResponse
from app.core.dependencies import (
    require_role,
    get_doctor_profile_service,
    get_doctor_availability_service,
)
from app.services.doctor_service import DoctorProfileService, DoctorAvailabilityService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=SuccessResponse,
    summary="Search Verified Doctors",
    description="Search and filter verified doctor profiles by name, specialization, and minimum years of experience.",
)
async def list_doctors(
    search: Optional[str] = None,
    specialization: Optional[str] = None,
    min_experience: Optional[int] = None,
    current_user: UserInDB = Depends(require_role(UserRole.PATIENT)),
    doctor_service: DoctorProfileService = Depends(get_doctor_profile_service),
) -> SuccessResponse:
    """
    Search verified doctors.
    Only allows active verified profiles from active doctor users.
    """
    try:
        doctors = await doctor_service.search_verified_doctors(
            name_query=search,
            specialization=specialization,
            min_experience=min_experience,
        )
        return SuccessResponse(
            success=True,
            message="Doctors retrieved successfully",
            data={"doctors": [doc.model_dump() for doc in doctors]},
        )
    except Exception as exc:
        logger.exception("Failed to search verified doctors")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search verified doctors",
        ) from exc


@router.get(
    "/{doctor_id}",
    response_model=SuccessResponse,
    summary="Get Doctor Details",
    description="Retrieve profile details for a specific active, verified doctor.",
)
async def get_doctor_details(
    doctor_id: str,
    current_user: UserInDB = Depends(require_role(UserRole.PATIENT)),
    doctor_service: DoctorProfileService = Depends(get_doctor_profile_service),
) -> SuccessResponse:
    """
    Get doctor profile details.
    Restricted to verified doctor status on active accounts.
    """
    try:
        doctor = await doctor_service.get_verified_doctor_by_id(doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found, inactive, or not verified",
            )
        return SuccessResponse(
            success=True,
            message="Doctor details retrieved successfully",
            data=doctor.model_dump(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve doctor details for profile %s", doctor_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve doctor details",
        ) from exc


@router.get(
    "/{doctor_id}/availability",
    response_model=SuccessResponse,
    summary="Get Doctor Available Slots",
    description="Retrieve future available consultation slots for a verified doctor.",
)
async def get_doctor_availability(
    doctor_id: str,
    current_user: UserInDB = Depends(require_role(UserRole.PATIENT)),
    doctor_service: DoctorProfileService = Depends(get_doctor_profile_service),
    availability_service: DoctorAvailabilityService = Depends(get_doctor_availability_service),
) -> SuccessResponse:
    """
    Retrieve future available slots for a doctor.
    Ensures doctor is active/verified, and filters out past or unavailable slots.
    """
    try:
        # Prevent slots listing from pending, rejected, or inactive doctors
        doctor = await doctor_service.get_verified_doctor_by_id(doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found, inactive, or not verified",
            )

        # Retrieve active availability slots
        slots = await availability_service.get_active_availability(doctor_id)

        # Filter out past/expired or unavailable slots in IST (UTC+05:30)
        ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        current_date_str = ist_now.strftime("%Y-%m-%d")
        current_time_str = ist_now.strftime("%H:%M")

        future_available_slots = []
        for slot in slots:
            # Active check
            if not slot.active or not slot.is_available:
                continue

            # Expiration date/time checks
            is_future_date = slot.date > current_date_str
            is_future_time = slot.date == current_date_str and slot.start_time >= current_time_str

            if is_future_date or is_future_time:
                future_available_slots.append(availability_service.to_response(slot))

        return SuccessResponse(
            success=True,
            message="Availability slots retrieved successfully",
            data={"slots": [s.model_dump() for s in future_available_slots]},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve availability slots for doctor profile %s", doctor_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve availability slots",
        ) from exc
