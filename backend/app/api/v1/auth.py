"""
Nura - Auth API Router
Authentication endpoints for user registration and OTP verification
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.core.dependencies import get_user_service, get_otp_service, get_email_service
from app.models import UserCreate, UserRole, AuthProvider, OTPPurpose
from app.schemas.auth import SuccessResponse, OTPVerify
from app.services import UserService, OTPService, EmailService

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
