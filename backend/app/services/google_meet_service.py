"""
Nura - Google Meet Service
Service for handling Google Meet OAuth 2.0 flow and creating Google Meet spaces
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import httpx
from app.core.config import settings
from app.repositories.system_integration_repository import SystemIntegrationRepository
from app.repositories.appointment_repository import AppointmentRepository

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_MEET_SPACE_API_URL = "https://meet.googleapis.com/v2/spaces"
GOOGLE_MEET_SCOPE = "https://www.googleapis.com/auth/meetings.space.created"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GoogleMeetService:
    """Service handling Google Meet OAuth 2.0 flow and space creation"""

    def __init__(
        self,
        system_integration_repository: SystemIntegrationRepository,
        appointment_repository: Optional[AppointmentRepository] = None,
    ):
        self.system_integration_repository = system_integration_repository
        self.appointment_repository = appointment_repository

    def authorize(self, state: Optional[str] = None) -> str:
        """Generate Google OAuth 2.0 authorization URL for Google Meet scope"""
        params = {
            "client_id": settings.GOOGLE_MEET_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_MEET_REDIRECT_URI,
            "response_type": "code",
            "scope": GOOGLE_MEET_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
        }
        if state:
            params["state"] = state

        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def handle_callback(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for OAuth tokens and persist refresh token in database"""
        if not settings.GOOGLE_MEET_CLIENT_ID or not settings.GOOGLE_MEET_CLIENT_SECRET:
            raise ValueError("Google Meet client ID or client secret is not configured in environment")

        payload = {
            "code": code,
            "client_id": settings.GOOGLE_MEET_CLIENT_ID,
            "client_secret": settings.GOOGLE_MEET_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_MEET_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=payload)
            if response.status_code != 200:
                logger.error("Failed to exchange code for tokens: %s", response.text)
                raise ValueError(f"Failed to exchange Google OAuth code: {response.text}")

            token_data = response.json()

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        if not access_token:
            raise ValueError("Google OAuth response did not contain an access_token")

        now = utc_now()
        expires_at = (now + timedelta(seconds=expires_in)).isoformat()

        # Load existing stored data to preserve refresh_token if not sent in re-auth
        existing = await self.system_integration_repository.get_integration("google_meet") or {}
        final_refresh_token = refresh_token or existing.get("refresh_token")

        integration_doc = {
            "access_token": access_token,
            "refresh_token": final_refresh_token,
            "expires_at": expires_at,
            "scope": token_data.get("scope", GOOGLE_MEET_SCOPE),
            "updated_at": now.isoformat(),
        }

        await self.system_integration_repository.save_integration("google_meet", integration_doc)
        logger.info("Google Meet OAuth authorization tokens updated successfully")
        return {
            "authorized": True,
            "has_refresh_token": bool(final_refresh_token),
            "expires_at": expires_at,
        }

    async def get_access_token(self) -> Optional[str]:
        """Get a valid access token using stored refresh token (refreshing if expired or missing)"""
        integration = await self.system_integration_repository.get_integration("google_meet") or {}
        access_token = integration.get("access_token")
        expires_at_str = integration.get("expires_at")
        refresh_token = integration.get("refresh_token")

        # Check if access token is still valid (with 60s buffer)
        if access_token and expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at > utc_now() + timedelta(seconds=60):
                    return access_token
            except Exception:
                pass

        if not refresh_token:
            logger.warning("No Google Meet refresh token found in database")
            return None

        if not settings.GOOGLE_MEET_CLIENT_ID or not settings.GOOGLE_MEET_CLIENT_SECRET:
            logger.warning("Google Meet client ID or secret missing for token refresh")
            return None

        payload = {
            "client_id": settings.GOOGLE_MEET_CLIENT_ID,
            "client_secret": settings.GOOGLE_MEET_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(GOOGLE_TOKEN_URL, data=payload)
                if response.status_code != 200:
                    logger.error("Failed to refresh Google Meet access token: %s", response.text)
                    return None

                token_data = response.json()
                new_access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                now = utc_now()
                expires_at = (now + timedelta(seconds=expires_in)).isoformat()

                if new_access_token:
                    integration["access_token"] = new_access_token
                    integration["expires_at"] = expires_at
                    integration["updated_at"] = now.isoformat()
                    await self.system_integration_repository.save_integration("google_meet", integration)
                    return new_access_token
        except Exception as exc:
            logger.exception("Error during Google Meet token refresh: %s", exc)

        return None

    async def create_meeting(self, appointment_id: str) -> Optional[str]:
        """Create a Google Meet space for an appointment. Returns meeting link or None if unconfigured/failed."""
        # 1. Duplicate check: If appointment already has meeting_link, return it
        if self.appointment_repository:
            appt = await self.appointment_repository.get(appointment_id)
            if appt and appt.meeting_link:
                logger.info("Appointment %s already has a meeting link: %s", appointment_id, appt.meeting_link)
                return appt.meeting_link

        # 2. Retrieve valid access token
        access_token = await self.get_access_token()
        if not access_token:
            logger.warning("Google Meet access token unavailable. Skipping meeting creation for appointment %s.", appointment_id)
            return None

        # 3. Call Google Meet REST API v2 to create space
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(GOOGLE_MEET_SPACE_API_URL, headers=headers, json={})
                if response.status_code not in (200, 201):
                    logger.error("Google Meet API error (status %s): %s", response.status_code, response.text)
                    return None

                data = response.json()
                meeting_link = data.get("meetingUri")
                if not meeting_link and "meetingCode" in data:
                    meeting_link = f"https://meet.google.com/{data['meetingCode']}"

                if meeting_link:
                    logger.info("Successfully created Google Meet space for appointment %s: %s", appointment_id, meeting_link)
                    return meeting_link
                else:
                    logger.error("Google Meet API response did not contain meetingUri: %s", data)
                    return None
        except Exception as exc:
            logger.exception("Failed to create Google Meet space for appointment %s: %s", appointment_id, exc)
            return None
