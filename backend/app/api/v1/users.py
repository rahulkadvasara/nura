"""
Nura - User APIs
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from typing import Optional
import os
import shutil
import time
import logging

from app.core.dependencies import get_current_user, get_user_service
from app.models.user import UserInDB, UserUpdate, UserResponse
from app.models.preferences import NotificationPreferencesUpdate, NotificationPreferencesResponse
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

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


@router.post("/avatar", response_model=UserResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Upload/update user profile picture avatar with format and size limit validation."""
    # Enforce standard security limits: jpg, jpeg, png, webp.
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats: jpg, jpeg, png, webp."
        )

    # Max file size: 5MB
    max_size = 5 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5MB limit."
        )
    await file.seek(0)

    # Save to uploads/avatars directory
    os.makedirs("uploads/avatars", exist_ok=True)
    filename = f"{current_user.id}_{int(time.time())}{ext}"
    filepath = os.path.join("uploads/avatars", filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # If the user already has a local avatar, delete it to save space
    if current_user.profile_picture:
        if "/uploads/avatars/" in current_user.profile_picture:
            old_filename = current_user.profile_picture.split("/uploads/avatars/")[-1]
            old_filepath = os.path.join("uploads/avatars", old_filename)
            if os.path.exists(old_filepath):
                try:
                    os.remove(old_filepath)
                except Exception as e:
                    logger.error(f"Failed to delete old avatar file: {e}")

    base_url = str(request.base_url)
    profile_url = f"{base_url}uploads/avatars/{filename}"
    
    updated_user = await user_service.update_user(current_user.id, UserUpdate(profile_picture=profile_url))
    return user_service.to_response(updated_user)


@router.delete("/avatar", response_model=UserResponse)
async def delete_avatar(
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Delete current user profile picture avatar and clean up local file if uploaded."""
    if current_user.profile_picture:
        if "/uploads/avatars/" in current_user.profile_picture:
            old_filename = current_user.profile_picture.split("/uploads/avatars/")[-1]
            old_filepath = os.path.join("uploads/avatars", old_filename)
            if os.path.exists(old_filepath):
                try:
                    os.remove(old_filepath)
                except Exception as e:
                    logger.error(f"Failed to delete old avatar file: {e}")

    updated_user = await user_service.update_user(current_user.id, UserUpdate(profile_picture=None))
    return user_service.to_response(updated_user)
