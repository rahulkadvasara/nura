"""
Nura - User APIs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.core.dependencies import get_current_user, get_user_service
from app.models.user import UserInDB, UserUpdate, UserResponse
from app.models.preferences import NotificationPreferencesUpdate, NotificationPreferencesResponse
from app.services.user_service import UserService

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get the current user's profile."""
    return user_service.to_response(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update the current user's profile."""
    # Prevent password update via this endpoint
    if update_data.password_hash is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update password via profile update endpoint"
        )
        
    updated_user = await user_service.update_user(current_user.id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    return user_service.to_response(updated_user)


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get the current user's notification preferences."""
    prefs = await user_service.get_user_preferences(current_user.id)
    return prefs


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    update_data: NotificationPreferencesUpdate,
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update the current user's notification preferences."""
    prefs = await user_service.update_user_preferences(current_user.id, update_data)
    return prefs
