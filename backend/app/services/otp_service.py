"""
Nura - OTP Service
Business logic for OTP generation and verification
"""

import logging
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.models import OTPVerificationCreate, OTPVerificationInDB, OTPPurpose
from app.repositories import OTPRepository

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OTPService:
    """Owns OTP generation, delivery (stub), and verification."""

    OTP_EXPIRY_MINUTES = 10
    OTP_LENGTH = 6
    RATE_LIMIT_COUNT = 3
    RATE_LIMIT_WINDOW_MINUTES = 5

    def __init__(self, otp_repository: OTPRepository):
        self.otp_repository = otp_repository

    # ------------------------------------------------------------------
    # Generation helpers
    # ------------------------------------------------------------------

    def generate_otp(self, length: int = OTP_LENGTH) -> str:
        """Return a cryptographically-random numeric OTP string."""
        return "".join(secrets.choice(string.digits) for _ in range(length))

    def calculate_expiry(self, minutes: int = OTP_EXPIRY_MINUTES) -> datetime:
        """Return the UTC datetime at which an OTP should expire."""
        return _utc_now() + timedelta(minutes=minutes)

    # ------------------------------------------------------------------
    # Core flows
    # ------------------------------------------------------------------

    async def create_otp(
        self,
        email: str,
        purpose: OTPPurpose,
        otp_length: int = OTP_LENGTH,
        expiry_minutes: int = OTP_EXPIRY_MINUTES,
    ) -> Tuple[str, OTPVerificationCreate]:
        """Build an OTP + its Pydantic create-schema (does NOT persist)."""
        raw_otp = self.generate_otp(otp_length)
        create = OTPVerificationCreate(
            email=email.lower().strip(),
            otp=raw_otp,
            purpose=purpose,
            expires_at=self.calculate_expiry(expiry_minutes),
            verified=False,
        )
        return raw_otp, create

    async def send_otp(
        self,
        email: str,
        purpose: OTPPurpose,
        otp_length: int = OTP_LENGTH,
        expiry_minutes: int = OTP_EXPIRY_MINUTES,
    ) -> Optional[str]:
        """Invalidate any existing OTP, generate a new one, persist it.

        Returns the raw OTP string so the caller can hand it to a delivery
        mechanism (email/SMS).  Returns None on error.
        """
        try:
            await self.otp_repository.invalidate(email, purpose)
            raw_otp, otp_create = await self.create_otp(
                email, purpose, otp_length, expiry_minutes
            )
            await self.otp_repository.create_otp(otp_create)
            return raw_otp
        except Exception:
            logger.exception("Failed to create OTP for %s / %s", email, purpose)
            return None

    async def verify_otp(
        self, email: str, otp: str, purpose: OTPPurpose
    ) -> Optional[OTPVerificationInDB]:
        """Verify an OTP and mark it as used. Returns None on failure."""
        return await self.otp_repository.verify_otp(email.lower().strip(), otp, purpose)

    async def is_otp_valid(self, email: str, otp: str, purpose: OTPPurpose) -> bool:
        """Return True if the OTP is valid (not yet verified, not expired)."""
        return await self.verify_otp(email, otp, purpose) is not None

    async def get_latest_otp(
        self, email: str, purpose: OTPPurpose
    ) -> Optional[OTPVerificationInDB]:
        return await self.otp_repository.get_latest(email, purpose)

    async def resend_otp(self, email: str, purpose: OTPPurpose) -> Optional[str]:
        """Alias for send_otp — invalidates old codes then issues a fresh one."""
        return await self.send_otp(email, purpose)

    async def cleanup_expired_otps(self) -> int:
        return await self.otp_repository.cleanup_expired_otps()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def validate_email_format(self, email: str) -> bool:
        """Basic structural email validation (not a substitute for Pydantic EmailStr)."""
        normalised = email.lower().strip()
        if "@" not in normalised:
            return False
        local, _, domain = normalised.partition("@")
        return bool(local) and bool(domain) and "." in domain

    async def rate_limit_check(self, email: str, purpose: OTPPurpose) -> bool:
        """Return True if the email is below the OTP request rate limit."""
        window_start = _utc_now() - timedelta(minutes=self.RATE_LIMIT_WINDOW_MINUTES)
        recent = await self.otp_repository.get_many(
            {
                "email": email.lower().strip(),
                "purpose": purpose,
                "created_at": {"$gt": window_start},
            }
        )
        return len(recent) < self.RATE_LIMIT_COUNT
