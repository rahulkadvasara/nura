"""
Nura - Admin Router
Endpoints for platform administrators to review and verify doctor onboarding applications.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.models.user import UserInDB, UserRole, UserResponse
from app.models.doctor import DoctorProfileStatus
from app.schemas.auth import SuccessResponse, TokenUser
from app.schemas.doctor import (
    AdminDoctorListResponse,
    DoctorVerificationResponse,
    DoctorApprovalRequest,
    DoctorRejectionRequest,
)
from app.schemas.admin import (
    AdminCreateRequest,
    AdminCreateResponse,
    AdminDetailResponse,
)
from app.schemas.observability import AuditLogCreateSchema, AuditLogResponse, AgentLogResponse
from app.core.dependencies import (
    require_role,
    get_user_service,
    get_doctor_profile_service,
    get_doctor_document_service,
    get_audit_log_service,
    get_agent_log_service,
    get_refresh_token_repository,
    get_current_user,
    get_auth_service,
    get_admin_analytics_service,
    get_system_monitor_service,
    get_maintenance_service,
)
from app.services.user_service import UserService
from app.services.doctor_service import DoctorProfileService, DoctorDocumentService
from app.services.audit_log_service import AuditLogService
from app.services.agent_log_service import AgentLogService
from app.services.auth_service import AuthService
from app.services.system_monitor_service import SystemMonitorService
from app.services.maintenance_service import MaintenanceService
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.models.user import UserUpdate




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
        action="DOCTOR_APPROVED",
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

    # 3. Create audit log
    audit_schema = AuditLogCreateSchema(
        user_id=current_user.id,
        action="DOCTOR_REJECTED",
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


@router.get(
    "/admins",
    response_model=SuccessResponse,
    summary="List Administrators",
    description="Retrieve a list of all administrators, sorted by creation date descending."
)
async def list_admins(
    user_service: UserService = Depends(get_user_service)
) -> SuccessResponse:
    try:
        admins = await user_service.list_admins()
        return SuccessResponse(
            success=True,
            message="Administrators retrieved successfully",
            data={"admins": [user_service.to_response(admin).model_dump() for admin in admins]}
        )
    except Exception as e:
        logger.exception("Failed to retrieve administrators")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve administrators"
        ) from e


@router.get(
    "/admins/{admin_id}",
    response_model=SuccessResponse,
    summary="Get Administrator Details",
    description="Retrieve profile details, account status, and recent audit log events for a specific administrator."
)
async def get_admin_details(
    admin_id: str,
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    admin = await user_service.get_user_by_id(admin_id)
    if not admin or admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator not found"
        )

    # Get recent audit logs involving this administrator
    logs = await audit_log_service.get_admin_audit_logs(admin_id)
    audit_responses = [audit_log_service.to_response(log) for log in logs]

    admin_details = AdminDetailResponse(
        profile=user_service.to_response(admin),
        account_status={
            "is_active": admin.is_active,
            "email_verified": admin.email_verified
        },
        audit_summary=audit_responses
    )

    return SuccessResponse(
        success=True,
        message="Administrator details retrieved successfully",
        data=admin_details.model_dump()
    )


@router.post(
    "/admins",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Administrator",
    description="Create a new administrator account. Generates a temporary password."
)
async def create_admin(
    body: AdminCreateRequest,
    request: Request,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    try:
        new_admin, temp_password = await user_service.create_admin(
            full_name=body.full_name,
            email=body.email
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

    # Create audit log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    audit_schema = AuditLogCreateSchema(
        user_id=current_user.id,
        action="ADMIN_CREATED",
        resource_type="admin",
        resource_id=new_admin.id,
        old_value=None,
        new_value={
            "email": new_admin.email,
            "full_name": new_admin.full_name,
            "role": new_admin.role.value if hasattr(new_admin.role, "value") else new_admin.role
        },
        ip_address=ip_address,
        user_agent=user_agent
    )
    await audit_log_service.create_log(audit_schema)

    response_data = AdminCreateResponse(
        id=new_admin.id,
        full_name=new_admin.full_name,
        email=new_admin.email,
        role=new_admin.role.value if hasattr(new_admin.role, "value") else new_admin.role,
        is_active=new_admin.is_active,
        email_verified=new_admin.email_verified,
        created_at=new_admin.created_at,
        temporary_password=temp_password
    )

    return SuccessResponse(
        success=True,
        message="Administrator created successfully",
        data=response_data.model_dump()
    )


@router.put(
    "/admins/{admin_id}/enable",
    response_model=SuccessResponse,
    summary="Enable Administrator",
    description="Reactivate a disabled administrator account."
)
async def enable_admin(
    admin_id: str,
    request: Request,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    admin = await user_service.get_user_by_id(admin_id)
    if not admin or admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator not found"
        )

    if admin.is_active:
        return SuccessResponse(
            success=True,
            message="Administrator account is already active"
        )

    # Enable user
    updated_admin = await user_service.update_user_role(admin_id, UserRole.ADMIN, is_active=True)
    if not updated_admin:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable administrator"
        )

    # Log audit event
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    audit_schema = AuditLogCreateSchema(
        user_id=current_user.id,
        action="ADMIN_ENABLED",
        resource_type="admin",
        resource_id=admin_id,
        old_value={"is_active": False},
        new_value={"is_active": True},
        ip_address=ip_address,
        user_agent=user_agent
    )
    await audit_log_service.create_log(audit_schema)

    return SuccessResponse(
        success=True,
        message="Administrator account enabled successfully"
    )


@router.put(
    "/admins/{admin_id}/disable",
    response_model=SuccessResponse,
    summary="Disable Administrator",
    description="Deactivate an administrator account, enforcing that the last active administrator cannot be disabled."
)
async def disable_admin(
    admin_id: str,
    request: Request,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    admin = await user_service.get_user_by_id(admin_id)
    if not admin or admin.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator not found"
        )

    if not admin.is_active:
        return SuccessResponse(
            success=True,
            message="Administrator account is already disabled"
        )

    # Enforce last active admin check
    active_admins = await user_service.count_active_admins()
    if active_admins <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable the last active administrator. At least one active administrator must remain."
        )

    # Disable user
    updated_admin = await user_service.update_user_role(admin_id, UserRole.ADMIN, is_active=False)
    if not updated_admin:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable administrator"
        )

    # Log audit event
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    audit_schema = AuditLogCreateSchema(
        user_id=current_user.id,
        action="ADMIN_DISABLED",
        resource_type="admin",
        resource_id=admin_id,
        old_value={"is_active": True},
        new_value={"is_active": False},
        ip_address=ip_address,
        user_agent=user_agent
    )
    await audit_log_service.create_log(audit_schema)

    return SuccessResponse(
        success=True,
        message="Administrator account disabled successfully"
    )


@router.get(
    "/security/sessions",
    response_model=SuccessResponse,
    summary="Get Administrative Sessions",
    description="Retrieve all sessions (active, expired, and revoked) for the current administrator."
)
async def get_security_sessions(
    current_user: UserInDB = Depends(get_current_user),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> SuccessResponse:
    # Only current admin can view their own sessions
    sessions = await token_repo.get_all_by_user(current_user.id)
    
    formatted_sessions = []
    for s in sessions:
        formatted_sessions.append({
            "id": s.id,
            "created_at": s.created_at.isoformat() if hasattr(s.created_at, "isoformat") else s.created_at,
            "expires_at": s.expires_at.isoformat() if hasattr(s.expires_at, "isoformat") else s.expires_at,
            "revoked": s.revoked,
            "last_activity": s.last_activity.isoformat() if hasattr(s.last_activity, "isoformat") else s.last_activity
        })
        
    return SuccessResponse(
        success=True,
        message="Sessions retrieved successfully",
        data={"sessions": formatted_sessions}
    )


@router.post(
    "/security/sessions/{session_id}/revoke",
    response_model=SuccessResponse,
    summary="Revoke Administrative Session",
    description="Revoke a specific administrative session by its ID."
)
async def revoke_security_session(
    session_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    session = await token_repo.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
        
    # Check ownership: admin can revoke any of their own sessions
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot revoke other users' sessions"
        )
        
    # Cannot revoke already revoked session
    if session.revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already revoked"
        )
        
    # Revoke session
    revoked = await token_repo.revoke_token(session_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )
        
    # Log ADMIN_SESSION_REVOKED audit event
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    audit_schema = AuditLogCreateSchema(
        user_id=current_user.id,
        action="ADMIN_SESSION_REVOKED",
        resource_type="session",
        resource_id=session_id,
        old_value={"revoked": False},
        new_value={"revoked": True},
        ip_address=ip_address,
        user_agent=user_agent
    )
    await audit_log_service.create_log(audit_schema)
    
    return SuccessResponse(
        success=True,
        message="Session revoked successfully"
    )


@router.get(
    "/users",
    response_model=SuccessResponse,
    summary="List and Query Users",
    description="Retrieve a list of platform users with search and role/active status filters."
)
async def list_users(
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    skip: int = 0,
    user_service: UserService = Depends(get_user_service),
) -> SuccessResponse:
    users = await user_service.list_users(
        search=search,
        role=role,
        is_active=is_active,
        limit=limit,
        skip=skip
    )
    return SuccessResponse(
        success=True,
        message="Users retrieved successfully",
        data={"users": [user_service.to_response(u).model_dump() for u in users]}
    )


@router.get(
    "/users/{user_id}",
    response_model=SuccessResponse,
    summary="Get User Profile",
    description="Retrieve profile details for a specific user account."
)
async def get_user_details(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
) -> SuccessResponse:
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return SuccessResponse(
        success=True,
        message="User profile retrieved successfully",
        data=user_service.to_response(user).model_dump()
    )


@router.put(
    "/users/{user_id}/activate",
    response_model=SuccessResponse,
    summary="Activate User Account",
    description="Re-enable a suspended user account."
)
async def activate_user(
    user_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.is_active:
        return SuccessResponse(
            success=True,
            message="User account is already active"
        )
        
    await user_service.update_user(user_id, UserUpdate(is_active=True))
    
    # Audit Log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_log_service.create_log(AuditLogCreateSchema(
        user_id=current_user.id,
        action="USER_ACTIVATED",
        resource_type="user",
        resource_id=user_id,
        old_value={"is_active": False},
        new_value={"is_active": True},
        ip_address=ip_address,
        user_agent=user_agent
    ))
    
    return SuccessResponse(
        success=True,
        message="User account activated successfully"
    )


@router.put(
    "/users/{user_id}/suspend",
    response_model=SuccessResponse,
    summary="Suspend User Account",
    description="Deactivate a user account and terminate all active sessions."
)
async def suspend_user(
    user_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not user.is_active:
        return SuccessResponse(
            success=True,
            message="User account is already suspended"
        )
        
    # Enforce lockout protection for admin self-suspension
    if user.role == UserRole.ADMIN:
        active_admins = await user_service.count_active_admins()
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot suspend the last active administrator. At least one active administrator must remain."
            )
            
    await user_service.update_user(user_id, UserUpdate(is_active=False))
    
    # Revoke sessions
    await auth_service.logout_all(user_id)
    
    # Audit Log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_log_service.create_log(AuditLogCreateSchema(
        user_id=current_user.id,
        action="USER_SUSPENDED",
        resource_type="user",
        resource_id=user_id,
        old_value={"is_active": True},
        new_value={"is_active": False},
        ip_address=ip_address,
        user_agent=user_agent
    ))
    
    return SuccessResponse(
        success=True,
        message="User account suspended successfully"
    )


@router.get(
    "/doctors",
    response_model=SuccessResponse,
    summary="List Doctors",
    description="Retrieve a list of platform doctors with filters."
)
async def list_doctors(
    status: Optional[str] = None,
    specialization: Optional[str] = None,
    verification_status: Optional[DoctorProfileStatus] = None,
    limit: int = 100,
    skip: int = 0,
    user_service: UserService = Depends(get_user_service),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
) -> SuccessResponse:
    # 1. Fetch profiles matching filters
    profile_query = {}
    if verification_status:
        profile_query["profile_status"] = verification_status.value if hasattr(verification_status, "value") else verification_status
    if specialization:
        profile_query["specialization"] = {"$regex": specialization, "$options": "i"}
    
    # Filter by user status if provided
    if status:
        user_filter = {"role": UserRole.DOCTOR.value}
        if status == "active":
            user_filter["is_active"] = True
        elif status in ("suspended", "inactive"):
            user_filter["is_active"] = False
        
        matching_users = await user_service.user_repository.get_many(user_filter, limit=10000)
        user_ids = [u.id for u in matching_users]
        profile_query["user_id"] = {"$in": user_ids}
        
    profiles = await doctor_profile_service.profile_repository.get_many(profile_query, limit=limit, skip=skip)
    
    # 2. Join user info
    doctor_list = []
    for p in profiles:
         user = await user_service.get_user_by_id(p.user_id)
         if not user:
             continue
         doctor_list.append(
             AdminDoctorListResponse(
                 id=p.id,
                 user_id=p.user_id,
                 full_name=user.full_name,
                 email=user.email,
                 specialization=p.specialization,
                 experience_years=p.experience_years,
                 consultation_fee=p.consultation_fee,
                 hospital=p.hospital,
                 license_number=p.license_number,
                 education=p.education,
                 profile_status=p.profile_status,
                 created_at=p.created_at,
                 is_active=user.is_active
             )
         )
         
    return SuccessResponse(
        success=True,
        message="Doctors retrieved successfully",
        data={"doctors": [doc.model_dump() for doc in doctor_list]}
    )


@router.put(
    "/doctors/{doctor_profile_id}/suspend",
    response_model=SuccessResponse,
    summary="Suspend Doctor",
    description="Suspend a doctor profile, deactivating their user account and terminating their active sessions."
)
async def suspend_doctor(
    doctor_profile_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    profile = await doctor_profile_service.get_profile_by_id(doctor_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )
    if profile.profile_status == DoctorProfileStatus.SUSPENDED:
        return SuccessResponse(
            success=True,
            message="Doctor profile is already suspended"
        )
        
    # Update doctor profile status
    await doctor_profile_service.profile_repository.update_status(doctor_profile_id, DoctorProfileStatus.SUSPENDED)
    
    # Deactivate associated user account
    await user_service.update_user(profile.user_id, UserUpdate(is_active=False))
    
    # Revoke sessions
    await auth_service.logout_all(profile.user_id)
    
    # Audit Log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_log_service.create_log(AuditLogCreateSchema(
        user_id=current_user.id,
        action="DOCTOR_SUSPENDED",
        resource_type="doctor_profile",
        resource_id=doctor_profile_id,
        old_value={"profile_status": profile.profile_status.value},
        new_value={"profile_status": DoctorProfileStatus.SUSPENDED.value, "is_active": False},
        ip_address=ip_address,
        user_agent=user_agent
    ))
    
    return SuccessResponse(
        success=True,
        message="Doctor practitioner suspended successfully"
    )


@router.put(
    "/doctors/{doctor_profile_id}/reactivate",
    response_model=SuccessResponse,
    summary="Reactivate Doctor",
    description="Restore access for a suspended doctor profile."
)
async def reactivate_doctor(
    doctor_profile_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    profile = await doctor_profile_service.get_profile_by_id(doctor_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )
    if profile.profile_status == DoctorProfileStatus.VERIFIED:
        return SuccessResponse(
            success=True,
            message="Doctor profile is already active/verified"
        )
        
    # Update doctor profile status to verified
    await doctor_profile_service.profile_repository.update_status(doctor_profile_id, DoctorProfileStatus.VERIFIED)
    
    # Reactivate associated user account
    await user_service.update_user(profile.user_id, UserUpdate(is_active=True))
    
    # Audit Log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_log_service.create_log(AuditLogCreateSchema(
        user_id=current_user.id,
        action="DOCTOR_REACTIVATED",
        resource_type="doctor_profile",
        resource_id=doctor_profile_id,
        old_value={"profile_status": profile.profile_status.value},
        new_value={"profile_status": DoctorProfileStatus.VERIFIED.value, "is_active": True},
        ip_address=ip_address,
        user_agent=user_agent
    ))
    
    return SuccessResponse(
        success=True,
        message="Doctor practitioner reactivated successfully"
    )


@router.get(
    "/analytics",
    response_model=SuccessResponse,
    summary="Get Platform Analytics",
    description="Retrieve platform-wide operational and financial analytics metrics."
)
async def get_platform_analytics(
    analytics_service = Depends(get_admin_analytics_service)
) -> SuccessResponse:
    try:
        data = await analytics_service.get_analytics()
        return SuccessResponse(
            success=True,
            message="Platform analytics retrieved successfully",
            data=data
        )
    except Exception as e:
        logger.exception("Failed to retrieve platform analytics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform analytics"
        ) from e


@router.get(
    "/logs/audit",
    response_model=SuccessResponse,
    summary="Get Audit Logs",
    description="Retrieve paginated list of all platform action audit trails with search and filters."
)
async def get_audit_logs(
    limit: int = 50,
    skip: int = 0,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    role: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    audit_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    try:
        logs, total = await audit_service.get_audit_logs_paginated(
            limit=limit,
            skip=skip,
            search=search,
            user_id=user_id,
            role=role,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
        )
        return SuccessResponse(
            success=True,
            message="Audit logs retrieved successfully",
            data={
                "logs": [audit_service.to_response(log).model_dump() for log in logs],
                "total": total,
                "limit": limit,
                "skip": skip
            }
        )
    except Exception as e:
        logger.exception("Failed to retrieve audit logs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        ) from e


@router.get(
    "/logs/audit/{log_id}",
    response_model=SuccessResponse,
    summary="Get Audit Log Detail",
    description="Retrieve the complete details of a single audit log entry by ID."
)
async def get_audit_log_detail(
    log_id: str,
    audit_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    log = await audit_service.get_log_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log entry not found"
        )
    return SuccessResponse(
        success=True,
        message="Audit log detail retrieved successfully",
        data=audit_service.to_response(log).model_dump()
    )


@router.get(
    "/logs/agents",
    response_model=SuccessResponse,
    summary="Get Agent Execution Logs",
    description="Retrieve paginated list of agent execution logs and workflow run latency metadata."
)
async def get_agent_logs(
    limit: int = 50,
    skip: int = 0,
    agent: Optional[str] = None,
    status_filter: Optional[str] = None,
    session: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_service: AgentLogService = Depends(get_agent_log_service),
) -> SuccessResponse:
    try:
        logs, total = await agent_service.get_agent_logs_paginated(
            limit=limit,
            skip=skip,
            agent=agent,
            status=status_filter,
            session=session,
            start_date=start_date,
            end_date=end_date,
        )
        return SuccessResponse(
            success=True,
            message="Agent logs retrieved successfully",
            data={
                "logs": [agent_service.to_response(log).model_dump() for log in logs],
                "total": total,
                "limit": limit,
                "skip": skip
            }
        )
    except Exception as e:
        logger.exception("Failed to retrieve agent logs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent logs"
        ) from e


@router.get(
    "/logs/agents/{log_id}",
    response_model=SuccessResponse,
    summary="Get Agent Log Detail",
    description="Retrieve full payload and trace checkpoints for a single agent execution log."
)
async def get_agent_log_detail(
    log_id: str,
    agent_service: AgentLogService = Depends(get_agent_log_service),
) -> SuccessResponse:
    log = await agent_service.get_log_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent log entry not found"
        )
    return SuccessResponse(
        success=True,
        message="Agent log detail retrieved successfully",
        data=agent_service.to_response(log).model_dump()
    )


@router.get(
    "/logs/authentication",
    response_model=SuccessResponse,
    summary="Get Authentication Logs",
    description="Retrieve paginated list of security audit events like logins, password resets, and revocations."
)
async def get_authentication_logs(
    limit: int = 50,
    skip: int = 0,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    audit_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    try:
        logs, total = await audit_service.get_auth_logs_paginated(
            limit=limit,
            skip=skip,
            search=search,
            start_date=start_date,
            end_date=end_date,
        )
        return SuccessResponse(
            success=True,
            message="Authentication logs retrieved successfully",
            data={
                "logs": [audit_service.to_response(log).model_dump() for log in logs],
                "total": total,
                "limit": limit,
                "skip": skip
            }
        )
    except Exception as e:
        logger.exception("Failed to retrieve authentication logs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve authentication logs"
        ) from e


# ---------------------------------------------------------------------------
# Platform Health & Maintenance Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/system/health",
    response_model=SuccessResponse,
    summary="Get System Health status",
    dependencies=[Depends(require_role(UserRole.ADMIN))]
)
async def get_system_health(
    monitor_service: SystemMonitorService = Depends(get_system_monitor_service)
) -> SuccessResponse:
    try:
        health_data = await monitor_service.check_health()
        return SuccessResponse(
            success=True,
            message="System health check completed successfully",
            data={"services": [sh.model_dump() for sh in health_data]}
        )
    except Exception as e:
        logger.exception("Failed to retrieve system health")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health"
        ) from e


@router.get(
    "/system/jobs",
    response_model=SuccessResponse,
    summary="Get Background Jobs status",
    dependencies=[Depends(require_role(UserRole.ADMIN))]
)
async def get_system_jobs(
    monitor_service: SystemMonitorService = Depends(get_system_monitor_service)
) -> SuccessResponse:
    try:
        jobs_data = await monitor_service.get_background_jobs()
        return SuccessResponse(
            success=True,
            message="Background jobs retrieved successfully",
            data=jobs_data.model_dump()
        )
    except Exception as e:
        logger.exception("Failed to retrieve background jobs status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve background jobs status"
        ) from e


@router.get(
    "/system/info",
    response_model=SuccessResponse,
    summary="Get System Information details",
    dependencies=[Depends(require_role(UserRole.ADMIN))]
)
async def get_system_info(
    monitor_service: SystemMonitorService = Depends(get_system_monitor_service)
) -> SuccessResponse:
    try:
        info_data = monitor_service.get_system_info()
        return SuccessResponse(
            success=True,
            message="System information retrieved successfully",
            data=info_data.model_dump()
        )
    except Exception as e:
        logger.exception("Failed to retrieve system info")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system info"
        ) from e


@router.post(
    "/system/maintenance/clear-sessions",
    response_model=SuccessResponse,
    summary="Clear Expired Sessions"
)
async def clear_expired_sessions(
    request: Request,
    maintenance_service: MaintenanceService = Depends(get_maintenance_service),
    audit_service: AuditLogService = Depends(get_audit_log_service),
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> SuccessResponse:
    try:
        deleted_count = await maintenance_service.clear_expired_sessions()
        
        # Log audit trail
        audit_schema = AuditLogCreateSchema(
            user_id=current_user.id,
            action="ADMIN_MAINTENANCE_CLEAR_SESSIONS",
            resource_type="system",
            resource_id=None,
            old_value=None,
            new_value={"deleted_count": deleted_count},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        await audit_service.create_log(audit_schema)
        
        return SuccessResponse(
            success=True,
            message=f"Expired sessions cleared successfully. Purged {deleted_count} tokens.",
            data={"deleted_count": deleted_count}
        )
    except Exception as e:
        logger.exception("Failed to clear expired sessions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear expired sessions"
        ) from e


@router.post(
    "/system/maintenance/clear-otps",
    response_model=SuccessResponse,
    summary="Clear Expired OTPs"
)
async def clear_expired_otps(
    request: Request,
    maintenance_service: MaintenanceService = Depends(get_maintenance_service),
    audit_service: AuditLogService = Depends(get_audit_log_service),
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> SuccessResponse:
    try:
        deleted_count = await maintenance_service.clear_expired_otps()
        
        # Log audit trail
        audit_schema = AuditLogCreateSchema(
            user_id=current_user.id,
            action="ADMIN_MAINTENANCE_CLEAR_OTPS",
            resource_type="system",
            resource_id=None,
            old_value=None,
            new_value={"deleted_count": deleted_count},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        await audit_service.create_log(audit_schema)
        
        return SuccessResponse(
            success=True,
            message=f"Expired OTPs cleared successfully. Purged {deleted_count} records.",
            data={"deleted_count": deleted_count}
        )
    except Exception as e:
        logger.exception("Failed to clear expired OTPs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear expired OTPs"
        ) from e


@router.post(
    "/system/maintenance/archive-notifications",
    response_model=SuccessResponse,
    summary="Archive Old Notifications"
)
async def archive_notifications(
    request: Request,
    retention_days: int = 30,
    maintenance_service: MaintenanceService = Depends(get_maintenance_service),
    audit_service: AuditLogService = Depends(get_audit_log_service),
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> SuccessResponse:
    try:
        archived_count = await maintenance_service.archive_notifications(retention_days=retention_days)
        
        # Log audit trail
        audit_schema = AuditLogCreateSchema(
            user_id=current_user.id,
            action="ADMIN_MAINTENANCE_ARCHIVE_NOTIFICATIONS",
            resource_type="system",
            resource_id=None,
            old_value=None,
            new_value={"archived_count": archived_count, "retention_days": retention_days},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        await audit_service.create_log(audit_schema)
        
        return SuccessResponse(
            success=True,
            message=f"Notifications archived successfully. Moved {archived_count} records to backups.",
            data={"archived_count": archived_count}
        )
    except Exception as e:
        logger.exception("Failed to archive notifications")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive notifications"
        ) from e


@router.post(
    "/system/maintenance/archive-audit-logs",
    response_model=SuccessResponse,
    summary="Archive Old Audit Logs"
)
async def archive_audit_logs(
    request: Request,
    retention_days: int = 90,
    maintenance_service: MaintenanceService = Depends(get_maintenance_service),
    audit_service: AuditLogService = Depends(get_audit_log_service),
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> SuccessResponse:
    try:
        archived_count = await maintenance_service.archive_audit_logs(retention_days=retention_days)
        
        # Log audit trail
        audit_schema = AuditLogCreateSchema(
            user_id=current_user.id,
            action="ADMIN_MAINTENANCE_ARCHIVE_AUDIT_LOGS",
            resource_type="system",
            resource_id=None,
            old_value=None,
            new_value={"archived_count": archived_count, "retention_days": retention_days},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        await audit_service.create_log(audit_schema)
        
        return SuccessResponse(
            success=True,
            message=f"Audit logs archived successfully. Moved {archived_count} records to backups.",
            data={"archived_count": archived_count}
        )
    except Exception as e:
        logger.exception("Failed to archive audit logs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive audit logs"
        ) from e




