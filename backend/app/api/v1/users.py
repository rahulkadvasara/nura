"""
Nura - User APIs
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from typing import Optional
import os
import shutil
import time
import logging

from app.core.dependencies import get_current_user, get_user_service, get_storage_service
from app.services.storage.storage_provider import StorageProvider
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
    """Retrieve the profile details of the currently authenticated user."""
    return user_service.to_response(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update profile details for the authenticated user."""
    updated_user = await user_service.update_user(current_user.id, update_data)
    return user_service.to_response(updated_user)


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Retrieve current notification preferences for the user."""
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
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageProvider = Depends(get_storage_service)
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

    # Clean up previous avatar from storage if exists
    if current_user.profile_picture_metadata:
        try:
            meta = current_user.profile_picture_metadata
            await storage_service.delete_file(
                bucket=meta.get("bucket", "avatars"),
                object_key=meta.get("object_key")
            )
        except Exception as e:
            logger.error(f"Failed to delete old avatar file using metadata: {e}")
    elif current_user.profile_picture:
        if "/uploads/avatars/" in current_user.profile_picture:
            try:
                old_filename = current_user.profile_picture.split("/uploads/avatars/")[-1]
                await storage_service.delete_file(bucket="avatars", object_key=old_filename)
            except Exception as e:
                logger.error(f"Failed to delete legacy old avatar file: {e}")

    filename = f"{current_user.id}_{int(time.time())}{ext}"
    
    # Upload file through the abstraction layer
    upload_res = await storage_service.upload_file(
        file=file.file,
        filename=filename,
        bucket="avatars",
        content_type=file.content_type
    )

    profile_url = upload_res["public_url"]
    
    updated_user = await user_service.update_user(
        current_user.id,
        UserUpdate(
            profile_picture=profile_url,
            profile_picture_metadata=upload_res
        )
    )
    return user_service.to_response(updated_user)


@router.delete("/avatar", response_model=UserResponse)
async def delete_avatar(
    current_user: UserInDB = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageProvider = Depends(get_storage_service)
):
    """Delete current user profile picture avatar and clean up file in storage provider."""
    if current_user.profile_picture_metadata:
        try:
            meta = current_user.profile_picture_metadata
            await storage_service.delete_file(
                bucket=meta.get("bucket", "avatars"),
                object_key=meta.get("object_key")
            )
        except Exception as e:
            logger.error(f"Failed to delete avatar file using metadata: {e}")
    elif current_user.profile_picture:
        if "/uploads/avatars/" in current_user.profile_picture:
            try:
                old_filename = current_user.profile_picture.split("/uploads/avatars/")[-1]
                await storage_service.delete_file(bucket="avatars", object_key=old_filename)
            except Exception as e:
                logger.error(f"Failed to delete legacy avatar file: {e}")

    updated_user = await user_service.update_user(
        current_user.id,
        UserUpdate(
            profile_picture=None,
            profile_picture_metadata=None
        )
    )
    return user_service.to_response(updated_user)
