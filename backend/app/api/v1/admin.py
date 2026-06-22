"""
Nura - Admin Router
Endpoints for platform administrators to review and verify doctor onboarding applications.
"""

import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import UserInDB, UserRole
from app.models.doctor import DoctorProfileStatus
from app.schemas.auth import SuccessResponse, TokenUser
from app.schemas.doctor import (
    AdminDoctorListResponse,
    DoctorVerificationResponse,
    DoctorApprovalRequest,
    DoctorRejectionRequest,
)
from app.schemas.observability import AuditLogCreateSchema
from app.core.dependencies import (
    require_role,
    get_user_service,
    get_doctor_profile_service,
    get_doctor_document_service,
    get_audit_log_service,
)
from app.services.user_service import UserService
from app.services.doctor_service import DoctorProfileService, DoctorDocumentService
from app.services.audit_log_service import AuditLogService

logger = logging.getLogger(__name__)

# Protect all endpoints in this router to be ADMIN only
router = APIRouter(dependencies=[Depends(require_role(UserRole.ADMIN))])


@router.get(
    "/doctors/pending",
    response_model=SuccessResponse,
    summary="Get Pending Doctor Applications",
    description="Retrieve list of all doctor onboarding applications currently awaiting review."
)
async def get_pending_doctors(
    user_service: UserService = Depends(get_user_service),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
) -> SuccessResponse:
    """
    List all pending applications with user profile data joined.
    """
    try:
        pending_profiles = await doctor_profile_service.list_by_status(DoctorProfileStatus.PENDING)
        
        list_items = []
        for profile in pending_profiles:
            user = await user_service.get_user_by_id(profile.user_id)
            if not user:
                continue
            
            list_items.append(
                AdminDoctorListResponse(
                    id=profile.id,
                    user_id=profile.user_id,
                    full_name=user.full_name,
                    email=user.email,
                    specialization=profile.specialization,
                    experience_years=profile.experience_years,
                    consultation_fee=profile.consultation_fee,
                    hospital=profile.hospital,
                    license_number=profile.license_number,
                    education=profile.education,
                    profile_status=profile.profile_status,
                    created_at=profile.created_at,
                )
            )

        return SuccessResponse(
            success=True,
            message="Pending applications retrieved successfully",
            data={"doctors": [item.model_dump() for item in list_items]}
        )
    except Exception as e:
        logger.exception("Failed to retrieve pending doctor applications")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending doctor applications"
        ) from e


@router.get(
    "/doctors/{doctor_profile_id}",
    response_model=SuccessResponse,
    summary="Get Doctor Application Details",
    description="Retrieve full details, documents, and applicant info for a specific doctor profile ID."
)
async def get_doctor_application_details(
    doctor_profile_id: str,
    user_service: UserService = Depends(get_user_service),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    doctor_document_service: DoctorDocumentService = Depends(get_doctor_document_service),
) -> SuccessResponse:
    """
    Get full details of a doctor application.
    """
    profile = await doctor_profile_service.get_profile_by_id(doctor_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    user = await user_service.get_user_by_id(profile.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user account not found"
        )

    docs = await doctor_document_service.get_documents_by_doctor(doctor_profile_id)

    # Convert TokenUser schema
    token_user = TokenUser(
        id=user.id,
        role=user.role,
        email=user.email,
        full_name=user.full_name,
        email_verified=user.email_verified,
    )

    response_data = DoctorVerificationResponse(
        profile=doctor_profile_service.to_response(profile),
        user=token_user,
        documents=[doctor_document_service.to_response(d) for d in docs]
    )

    return SuccessResponse(
        success=True,
        message="Doctor application details retrieved successfully",
        data=response_data.model_dump()
    )


@router.post(
    "/doctors/{doctor_profile_id}/approve",
    response_model=SuccessResponse,
    summary="Approve Doctor Application",
    description="Verify doctor credentials, approve documents, promote user to DOCTOR, and create audit log."
)
async def approve_doctor_application(
    doctor_profile_id: str,
    body: DoctorApprovalRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    doctor_document_service: DoctorDocumentService = Depends(get_doctor_document_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    """
    Approve doctor credentials. Promotes user's role to DOCTOR and logs the event.
    """
    profile = await doctor_profile_service.get_profile_by_id(doctor_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    user = await user_service.get_user_by_id(profile.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user account not found"
        )

    # 1. Update doctor profile verification status to verified
    updated_profile = await doctor_profile_service.verify_profile(doctor_profile_id)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update doctor profile status"
        )

    # 2. Update all pending verification documents to approved
    docs = await doctor_document_service.get_documents_by_doctor(doctor_profile_id)
    for doc in docs:
        await doctor_document_service.approve_document(doc.id, current_user.id)

    # 3. Promote user role to doctor and ensure account is active
    await user_service.update_user_role(profile.user_id, UserRole.DOCTOR, is_active=True)

    # 4. Create audit log
    audit_schema = AuditLogCreateSchema(
        user_id=current_user.id,
        action="doctor_approved",
        resource_type="doctor_profile",
        resource_id=doctor_profile_id,
        old_value={"profile_status": profile.profile_status.value},
        new_value={"profile_status": DoctorProfileStatus.VERIFIED.value, "promoted_role": UserRole.DOCTOR.value, "target_user_id": profile.user_id},
    )
    await audit_log_service.create_log(audit_schema)

    return SuccessResponse(
        success=True,
        message="Doctor application approved and user promoted successfully"
    )


@router.post(
    "/doctors/{doctor_profile_id}/reject",
    response_model=SuccessResponse,
    summary="Reject Doctor Application",
    description="Mark doctor profile and documents as rejected with reason, and log the event. User remains PATIENT."
)
async def reject_doctor_application(
    doctor_profile_id: str,
    body: DoctorRejectionRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    doctor_document_service: DoctorDocumentService = Depends(get_doctor_document_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    """
    Reject doctor credentials. Stores rejection reason and logs the event.
    """
    profile = await doctor_profile_service.get_profile_by_id(doctor_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # 1. Update doctor profile status to rejected with reason
    updated_profile = await doctor_profile_service.reject_profile(doctor_profile_id, body.rejection_reason)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update doctor profile status"
        )

    # 2. Update all pending verification documents to rejected
    docs = await doctor_document_service.get_documents_by_doctor(doctor_profile_id)
    for doc in docs:
        await doctor_document_service.reject_document(doc.id, current_user.id)

    # 3. Create audit log
    audit_schema = AuditLogCreateSchema(
        user_id=current_user.id,
        action="doctor_rejected",
        resource_type="doctor_profile",
        resource_id=doctor_profile_id,
        old_value={"profile_status": profile.profile_status.value},
        new_value={"profile_status": DoctorProfileStatus.REJECTED.value, "rejection_reason": body.rejection_reason, "target_user_id": profile.user_id},
    )
    await audit_log_service.create_log(audit_schema)

    return SuccessResponse(
        success=True,
        message="Doctor application rejected successfully"
    )
