import io
import os
import hashlib
import logging
from typing import Tuple
from PIL import Image, ImageOps
from fastapi import HTTPException, status

logger = logging.getLogger("nura.storage.utils")

ALLOWED_AVATAR_MIMES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_AVATAR_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB

def calculate_sha256(content: bytes) -> str:
    """Calculate the SHA-256 checksum of binary file content."""
    sha = hashlib.sha256()
    sha.update(content)
    return sha.hexdigest()

def optimize_avatar(content: bytes, filename: str, content_type: str) -> Tuple[bytes, str, str]:
    """
    Validates, resizes, converts to WebP, and compresses an avatar image.
    
    Args:
        content: Raw file bytes.
        filename: Original uploaded filename.
        content_type: Original file content type.
        
    Returns:
        Tuple[bytes, str, str]: (optimized_bytes, new_filename, webp_content_type)
    """
    # 1. Size Validation
    if len(content) > MAX_AVATAR_SIZE:
        logger.warning(f"Avatar upload rejected: size {len(content)} exceeds 5MB limit")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of 5MB (got {len(content) / (1024*1024):.2f}MB)"
        )
        
    # 2. Format / Extension Validation
    ext = os.path.splitext(filename)[1].lower()
    if content_type.lower() not in ALLOWED_AVATAR_MIMES and ext not in ALLOWED_AVATAR_EXTS:
        logger.warning(f"Avatar upload rejected: unsupported format {content_type} / {ext}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Allowed formats: JPG, JPEG, PNG, WEBP (got {ext})"
        )
        
    # 3. Image Processing using Pillow
    try:
        image = Image.open(io.BytesIO(content))
        
        # Transpose image based on EXIF orientation if present
        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass
            
        # Resize to max 800px width/height while preserving aspect ratio
        max_size = 800
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        # Compress and save as WebP
        out_buf = io.BytesIO()
        image.save(out_buf, format="WEBP", quality=80)
        optimized_bytes = out_buf.getvalue()
        
        logger.info(f"Successfully optimized avatar from {len(content)} to {len(optimized_bytes)} bytes (WebP)")
        return optimized_bytes, "avatar.webp", "image/webp"
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image processing pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process and optimize image: {str(e)}"
        )
