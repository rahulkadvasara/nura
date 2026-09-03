"""
Nura - Integrations Router
API endpoints for Google Meet OAuth 2.0 authorization and callbacks
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.schemas.auth import SuccessResponse
from app.core.dependencies import get_google_meet_service
from app.services.google_meet_service import GoogleMeetService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/google/authorize",
    summary="Authorize Google Meet Integration",
    description="Generates the Google OAuth 2.0 authorization URL for Google Meet.",
)
async def google_authorize(
    redirect: bool = Query(default=False, description="If true, HTTP 307 redirects directly to Google auth page"),
    state: Optional[str] = Query(default=None, description="Optional state parameter"),
    service: GoogleMeetService = Depends(get_google_meet_service),
):
    """Initiates Google Meet OAuth 2.0 authorization flow"""
    try:
        auth_url = service.authorize(state=state)
        if redirect:
            return RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

        return SuccessResponse(
            success=True,
            message="Google Meet authorization URL generated",
            data={"authorize_url": auth_url},
        )
    except Exception as exc:
        logger.exception("Failed to generate Google Meet authorization URL")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Google Meet authorization URL",
        ) from exc


@router.get(
    "/google/callback",
    summary="Google Meet OAuth Callback",
    description="Receives Google OAuth authorization code, exchanges it for tokens, and persists the refresh token.",
)
async def google_callback(
    code: Optional[str] = Query(default=None, description="Google OAuth authorization code"),
    error: Optional[str] = Query(default=None, description="OAuth error message if authorization failed"),
    service: GoogleMeetService = Depends(get_google_meet_service),
):
    """Handles Google Meet OAuth callback"""
    if error:
        logger.error("Google OAuth error in callback: %s", error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth authorization failed: {error}",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'code' query parameter in OAuth callback",
        )

    try:
        result = await service.handle_callback(code)
        return SuccessResponse(
            success=True,
            message="Google Meet OAuth integration authorized and refresh token stored successfully",
            data=result,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to process Google Meet OAuth callback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete Google Meet OAuth authorization",
        ) from exc
