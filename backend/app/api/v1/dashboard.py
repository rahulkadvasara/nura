"""
Nura - Dashboard API Router
Role-guarded dashboard endpoints for Patient, Doctor, and Admin
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import UserInDB, UserRole
from app.schemas.auth import SuccessResponse
from app.schemas.dashboard import (
    PatientDashboardResponse,
    DoctorDashboardResponse,
    AdminDashboardResponse,
)
from app.core.dependencies import (
    require_role,
    get_patient_dashboard_service,
    get_doctor_dashboard_service,
    get_admin_dashboard_service,
    get_doctor_profile_service,
)
from app.services.patient_dashboard_service import PatientDashboardService
from app.services.doctor_dashboard_service import DoctorDashboardService
from app.services.admin_dashboard_service import AdminDashboardService
from app.services.doctor_service import DoctorProfileService
from app.models.doctor import DoctorProfileStatus


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/patient",
    response_model=SuccessResponse,
    summary="Patient Dashboard",
    description="Returns aggregated healthcare data for the authenticated patient.",
)
async def patient_dashboard(
    current_user: UserInDB = Depends(require_role(UserRole.PATIENT)),
    dashboard_service: PatientDashboardService = Depends(get_patient_dashboard_service),
) -> SuccessResponse:
    """
    Retrieve patient dashboard data.
    Requires PATIENT role.
    Returns:
    - upcoming_appointments_count
    - active_reminders_count
    - reports_count
    - unread_notifications_count
    - recent_health_insights (last 5)
    """
    try:
        summary = await dashboard_service.get_dashboard(current_user.id)
    except Exception as exc:
        logger.exception("Failed to retrieve patient dashboard for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient dashboard",
        ) from exc

    return SuccessResponse(
        success=True,
        message="Patient dashboard retrieved",
        data=summary.model_dump(),
    )


@router.get(
    "/doctor",
    response_model=SuccessResponse,
    summary="Doctor Dashboard",
    description="Returns aggregated practice data for the authenticated doctor.",
)
async def doctor_dashboard(
    current_user: UserInDB = Depends(require_role(UserRole.DOCTOR)),
    dashboard_service: DoctorDashboardService = Depends(get_doctor_dashboard_service),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
) -> SuccessResponse:
    """
    Retrieve doctor dashboard data.
    Requires DOCTOR role.
    Returns:
    - todays_appointments_count
    - upcoming_appointments_count
    - total_patients_count
    - pending_approvals_count
    - wallet_balance
    - total_earnings
    """
    # Enforce suspended doctor block
    profile = await doctor_profile_service.get_profile_by_user_id(current_user.id)
    if profile and profile.profile_status == DoctorProfileStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor profile is suspended"
        )

    try:
        summary = await dashboard_service.get_dashboard(current_user.id)
    except Exception as exc:
        logger.exception("Failed to retrieve doctor dashboard for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve doctor dashboard",
        ) from exc


    return SuccessResponse(
        success=True,
        message="Doctor dashboard retrieved",
        data=summary.model_dump(),
    )


@router.get(
    "/admin",
    response_model=SuccessResponse,
    summary="Admin Dashboard",
    description="Returns aggregated platform-wide metrics for the authenticated admin.",
)
async def admin_dashboard(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    dashboard_service: AdminDashboardService = Depends(get_admin_dashboard_service),
) -> SuccessResponse:
    """
    Retrieve admin dashboard data.
    Requires ADMIN role.
    Returns:
    - total_users_count
    - total_patients_count
    - total_doctors_count
    - pending_doctor_verifications_count
    - total_appointments_count
    - total_revenue
    - active_consultations_count
    """
    try:
        summary = await dashboard_service.get_dashboard()
    except Exception as exc:
        logger.exception("Failed to retrieve admin dashboard for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin dashboard",
        ) from exc

    return SuccessResponse(
        success=True,
        message="Admin dashboard retrieved",
        data=summary.model_dump(),
    )
