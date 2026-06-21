"""
Nura - Auth API Router
Authentication endpoints for user registration and OTP verification
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.core.dependencies import get_user_service, get_otp_service, get_email_service, get_auth_service, require_active_user
from app.models import UserCreate, UserRole, AuthProvider, OTPPurpose, UserInDB
from app.schemas.auth import SuccessResponse, OTPVerify, UserLogin, RefreshTokenRequest
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
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
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

    # Generate tokens
    token_response, raw_refresh, refresh_token_create = await auth_service._build_token_pair(user)

    # Store refresh token in MongoDB
    await auth_service.refresh_token_repository.create_token(refresh_token_create)

    return SuccessResponse(
        success=True,
        message="Login successful",
        data={
            "access_token": token_response.access_token,
            "refresh_token": token_response.refresh_token,
            "user": {
                "id": token_response.user.id,
                "role": token_response.user.role.value,
            }
        }
    )


@router.post("/refresh", response_model=SuccessResponse)
async def refresh(
    refresh_in: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
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
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Logout user by revoking their refresh token
    """
    token_hash = auth_service.hash_token(refresh_in.refresh_token)
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

