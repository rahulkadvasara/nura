"""
Nura - Auth API Router
Authentication endpoints for user registration and OTP verification
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import ValidationError
from datetime import datetime, timezone

from app.core.config import settings
from app.core.dependencies import (
    get_user_service,
    get_otp_service,
    get_email_service,
    get_auth_service,
    require_active_user,
    get_audit_log_service,
)
from app.models import UserCreate, UserRole, AuthProvider, OTPPurpose, UserInDB, OTPVerificationInDB
from app.schemas.auth import (
    SuccessResponse,
    OTPVerify,
    UserLogin,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    GoogleLoginRequest,
    ChangePasswordRequest,
)
from app.schemas.observability import AuditLogCreateSchema
from app.services import UserService, OTPService, EmailService, AuthService

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service),
    otp_service: OTPService = Depends(get_otp_service),
    email_service: EmailService = Depends(get_email_service),
):
    """
    Register a new user and send verification OTP
    """
    email = user_in.email.lower().strip()

    # Check email uniqueness
    if await user_service.user_exists(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Force inactive status until email is verified
    user_in.is_active = False
    user_in.email_verified = False
    user_in.role = UserRole.PATIENT  # default to patient for register
    user_in.auth_provider = AuthProvider.LOCAL

    try:
        # Create user
        await user_service.create_user(user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Generate OTP
    otp = await otp_service.send_otp(email, OTPPurpose.REGISTRATION)
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate verification OTP",
        )

    # Send OTP Email
    email_sent = await email_service.send_otp_email(email, otp, "registration")
    if not email_sent:
        logger.warning(f"Could not send OTP email to {email}")

    return SuccessResponse(
        success=True,
        message="OTP sent successfully",
    )


@router.post("/verify-otp", response_model=SuccessResponse)
async def verify_otp(
    verify_in: OTPVerify,
    user_service: UserService = Depends(get_user_service),
    otp_service: OTPService = Depends(get_otp_service),
):
    """
    Verify user OTP and activate account
    """
    email = verify_in.email.lower().strip()

    # Get user
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already verified
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already verified",
        )

    # Get latest OTP for detailed error messaging
    latest_otp = await otp_service.get_latest_otp(email, OTPPurpose.REGISTRATION)
    if not latest_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    # Attempt to atomically verify the OTP
    verified_otp = await otp_service.verify_otp(email, verify_in.otp, OTPPurpose.REGISTRATION)
    if not verified_otp:
        # Check if the OTP is invalid or expired
        if latest_otp.otp != verify_in.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expired OTP",
            )

    # Activate user and mark email as verified
    await user_service.verify_user_email(user.id)
    # We update is_active=True using UserUpdate model
    from app.models import UserUpdate
    await user_service.update_user(user.id, UserUpdate(is_active=True))

    return SuccessResponse(
        success=True,
        message="Account verified",
    )


@router.post("/login", response_model=SuccessResponse)
async def login(
    login_in: UserLogin,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service = Depends(get_audit_log_service),
):
    """
    Authenticate a user, issue access and refresh tokens
    """
    email = login_in.email.lower().strip()
    password = login_in.password

    # Find user
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    # Verify password
    if not user_service.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    # Verify account active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive",
        )

    # Verify email verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )

    # Update last_login_at
    from app.models.user import UserUpdate
    await user_service.update_user(user.id, UserUpdate(last_login_at=datetime.now(timezone.utc)))

    # Generate tokens
    token_response, raw_refresh, refresh_token_create = await auth_service._build_token_pair(user)

    # Store refresh token in MongoDB
    await auth_service.refresh_token_repository.create_token(refresh_token_create)

    # Log ADMIN_LOGIN audit event
    if user.role == UserRole.ADMIN:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await audit_log_service.create_log(AuditLogCreateSchema(
            user_id=user.id,
            action="ADMIN_LOGIN",
            resource_type="admin",
            resource_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        ))


    return SuccessResponse(
        success=True,
        message="Login successful",
        data={
            "access_token": token_response.access_token,
            "refresh_token": token_response.refresh_token,
            "user": {
                "id": token_response.user.id,
                "role": token_response.user.role.value,
                "email": token_response.user.email,
                "full_name": token_response.user.full_name,
                "email_verified": token_response.user.email_verified,
            }
        }
    )


@router.post("/refresh", response_model=SuccessResponse)
async def refresh(
    refresh_in: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service = Depends(get_audit_log_service),
):
    """
    Refresh JWT access token using opaque refresh token
    """
    token_hash = auth_service.hash_token(refresh_in.refresh_token)
    record = await auth_service.refresh_token_repository.get_by_token_hash(token_hash)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if record.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    from datetime import datetime, timezone
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    user = await auth_service.user_service.get_user_by_id(record.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # If user is admin, update last activity and log event
    if user.role == UserRole.ADMIN:
        await auth_service.refresh_token_repository.update_last_activity(record.id)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await audit_log_service.create_log(AuditLogCreateSchema(
            user_id=user.id,
            action="ADMIN_TOKEN_REFRESH",
            resource_type="admin",
            resource_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        ))

    # Generate new access token ONLY (no rotation)
    new_access = auth_service.create_access_token(user)

    return SuccessResponse(
        success=True,
        message="Token refreshed successfully",
        data={
            "access_token": new_access
        }
    )



@router.post("/logout", response_model=SuccessResponse)
async def logout(
    refresh_in: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service = Depends(get_audit_log_service),
):
    """
    Logout user by revoking their refresh token
    """
    token_hash = auth_service.hash_token(refresh_in.refresh_token)
    
    # Retrieve user before revoking token
    record = await auth_service.refresh_token_repository.get_by_token_hash(token_hash)
    if record:
        user = await auth_service.user_service.get_user_by_id(record.user_id)
        if user and user.role == UserRole.ADMIN:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            await audit_log_service.create_log(AuditLogCreateSchema(
                user_id=user.id,
                action="ADMIN_LOGOUT",
                resource_type="admin",
                resource_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            ))

    revoked = await auth_service.refresh_token_repository.revoke_by_hash(token_hash)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already revoked refresh token",
        )

    return SuccessResponse(
        success=True,

        message="Logged out successfully",
    )


@router.get("/me", response_model=SuccessResponse)
async def get_me(
    current_user: UserInDB = Depends(require_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get current authenticated user profile
    """
    user_response = user_service.to_response(current_user)
    return SuccessResponse(
        success=True,
        message="User profile retrieved",
        data=user_response.model_dump(),
    )


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    forgot_in: ForgotPasswordRequest,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    otp_service: OTPService = Depends(get_otp_service),
    email_service: EmailService = Depends(get_email_service),
    audit_log_service = Depends(get_audit_log_service),
):
    """
    Initiate password recovery by sending an OTP to the user's email (enumeration prevention)
    """
    email = forgot_in.email.lower().strip()

    # Look up user
    user = await user_service.get_user_by_email(email)
    
    # Generic message for enumeration prevention
    success_message = "If this email is registered, we have sent a password reset OTP"

    if not user:
        # Return generic success immediately to prevent account enumeration
        return SuccessResponse(
            success=True,
            message=success_message,
        )

    # Generate OTP for password reset
    otp = await otp_service.send_otp(email, OTPPurpose.PASSWORD_RESET)
    if not otp:
        # Log error internally but return success to client
        logger.error(f"Failed to generate password reset OTP for {email}")
        return SuccessResponse(
            success=True,
            message=success_message,
        )

    # Log ADMIN_PASSWORD_RESET_REQUEST audit event
    if user.role == UserRole.ADMIN:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await audit_log_service.create_log(AuditLogCreateSchema(
            user_id=user.id,
            action="ADMIN_PASSWORD_RESET_REQUEST",
            resource_type="admin",
            resource_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        ))

    # Send password reset email
    email_sent = await email_service.send_password_reset_email(email, otp)
    if not email_sent:
        logger.warning(f"Could not send password reset OTP email to {email}")

    return SuccessResponse(
        success=True,
        message=success_message,
    )



@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    reset_in: ResetPasswordRequest,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    otp_service: OTPService = Depends(get_otp_service),
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service = Depends(get_audit_log_service),
):
    """
    Reset user password using verification OTP
    """
    email = reset_in.email.lower().strip()

    # Look up the absolute latest OTP document to verify custom errors
    latest_otp_doc = await otp_service.otp_repository.collection.find_one(
        {"email": email, "purpose": OTPPurpose.PASSWORD_RESET},
        sort=[("created_at", -1)]
    )

    # Differentiate errors without leaking account existence for mismatching cases
    if not latest_otp_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    latest_otp = OTPVerificationInDB.from_mongo(latest_otp_doc)

    if latest_otp.otp != reset_in.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    if latest_otp.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has already been verified",
        )

    from datetime import datetime, timezone
    expires_at = latest_otp.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expired OTP",
        )

    # Find the user
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    # Perform verification (marks the OTP as verified)
    verified_otp = await otp_service.verify_otp(email, reset_in.otp, OTPPurpose.PASSWORD_RESET)
    if not verified_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification failed",
        )

    # Unconditionally reset user password (validation is handled inside the request schema and reset_password)
    password_updated = await user_service.reset_password(user.id, reset_in.new_password)
    if not password_updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    # Revoke all active refresh tokens belonging to the user (forces logout on all devices)
    await auth_service.logout_all(user.id)

    # Log ADMIN_PASSWORD_RESET_SUCCESS audit event
    if user.role == UserRole.ADMIN:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await audit_log_service.create_log(AuditLogCreateSchema(
            user_id=user.id,
            action="ADMIN_PASSWORD_RESET_SUCCESS",
            resource_type="admin",
            resource_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        ))


    return SuccessResponse(
        success=True,
        message="Password has been reset successfully",
    )


@router.post("/google", response_model=SuccessResponse)
async def google_login(
    google_in: GoogleLoginRequest,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user using Google ID token, creating profile if necessary
    """
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests

        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            google_in.id_token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        # Validate issuer
        if idinfo.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer")

        # Validate email verification claim
        if not idinfo.get("email_verified"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google email is not verified",
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Google token: {str(e)}",
        )

    email = idinfo.get("email").lower().strip()
    full_name = idinfo.get("name")
    profile_picture = idinfo.get("picture")

    # Look up user
    user = await user_service.get_user_by_email(email)

    if user:
        # Existing user flow
        # Ensure account is active and email is marked verified
        if not user.email_verified:
            await user_service.verify_user_email(user.id)
            
        update_data = {}
        if not user.is_active:
            update_data["is_active"] = True
        if profile_picture and not user.profile_picture:
            update_data["profile_picture"] = profile_picture
            
        if update_data:
            from app.models import UserUpdate
            await user_service.update_user(user.id, UserUpdate(**update_data))
            
        # Re-fetch user to make sure we return correct state
        user = await user_service.get_user_by_id(user.id)
    else:
        # New user flow
        user = await user_service.create_oauth_user(
            email=email,
            full_name=full_name,
            profile_picture=profile_picture,
            provider=AuthProvider.GOOGLE,
        )

    # Update last_login_at
    from app.models.user import UserUpdate
    await user_service.update_user(user.id, UserUpdate(last_login_at=datetime.now(timezone.utc)))

    # Issue access and refresh tokens
    token_response, raw_refresh, refresh_token_create = await auth_service._build_token_pair(user)

    # Store refresh token in MongoDB
    await auth_service.refresh_token_repository.create_token(refresh_token_create)

    return SuccessResponse(
        success=True,
        message="Google login successful",
        data={
            "access_token": token_response.access_token,
            "refresh_token": token_response.refresh_token,
            "user": {
                "id": token_response.user.id,
                "role": token_response.user.role.value,
                "email": token_response.user.email,
                "full_name": token_response.user.full_name,
                "email_verified": token_response.user.email_verified,
            }
        }
    )


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: UserInDB = Depends(require_active_user),
    user_service: UserService = Depends(get_user_service),
    audit_log_service = Depends(get_audit_log_service),
):
    """
    Change user password for logged-in users
    """
    success = await user_service.change_password(
        current_user.id, body.old_password, body.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    if current_user.role == UserRole.ADMIN:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await audit_log_service.create_log(AuditLogCreateSchema(
            user_id=current_user.id,
            action="ADMIN_PASSWORD_CHANGED",
            resource_type="admin",
            resource_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent
        ))
        
    return SuccessResponse(
        success=True,
        message="Password changed successfully"
    )


