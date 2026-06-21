"""
Nura - Auth Service
Business logic for JWT authentication and token management
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from jose import jwt, JWTError
import hashlib

from app.core.config import settings
from app.models import UserInDB, UserRole, RefreshTokenCreate
from app.schemas import TokenResponse, TokenUser
from app.repositories import RefreshTokenRepository
from app.services.user_service import UserService





def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    """Handles JWT creation/validation and refresh-token lifecycle."""

    def __init__(
        self,
        user_service: UserService,
        refresh_token_repository: RefreshTokenRepository,
    ):
        self.user_service = user_service
        self.refresh_token_repository = refresh_token_repository

    # ------------------------------------------------------------------
    # Access token
    # ------------------------------------------------------------------

    def create_access_token(self, user: UserInDB) -> str:
        """Return a signed JWT access token for *user*."""
        now = _utc_now()
        expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload: Dict[str, Any] = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "iat": now,
            "exp": expires,
            "type": "access",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT access token.  Returns the payload or None."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "access":
                return None
            return payload
        except JWTError:
            return None

    # ------------------------------------------------------------------
    # Refresh token
    # ------------------------------------------------------------------

    def create_refresh_token(self) -> Tuple[str, datetime]:
        """Generate a cryptographically-random refresh token and its expiry."""
        token = secrets.token_urlsafe(64)
        expires_at = _utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return token, expires_at

    def hash_token(self, token: str) -> str:
        """Return a SHA-256 hash of an opaque token string."""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def verify_token_hash(self, token: str, hashed_token: str) -> bool:
        """Return True when *token* matches *hashed_token*."""
        return self.hash_token(token) == hashed_token

    # ------------------------------------------------------------------
    # High-level auth flows
    # ------------------------------------------------------------------

    async def _build_token_pair(
        self, user: UserInDB
    ) -> Tuple[TokenResponse, str, RefreshTokenCreate]:
        """Create an access token + refresh token for *user*.

        Returns:
            (TokenResponse, raw_refresh_token_str, RefreshTokenCreate)
        """
        access_token = self.create_access_token(user)
        raw_refresh, expires_at = self.create_refresh_token()

        refresh_token_create = RefreshTokenCreate(
            user_id=user.id,
            token_hash=self.hash_token(raw_refresh),
            expires_at=expires_at,
            revoked=False,
        )

        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=TokenUser(
                id=user.id,
                role=user.role,
                email=user.email,
                full_name=user.full_name,
                email_verified=user.email_verified,
            ),
        )
        return token_response, raw_refresh, refresh_token_create

    async def login(
        self, email: str, password: str
    ) -> Optional[Tuple[TokenResponse, RefreshTokenCreate]]:
        """Authenticate with email/password and return a token pair.

        Returns None if authentication fails.
        """
        user = await self.user_service.authenticate_user(email, password)
        if not user:
            return None

        token_response, _, refresh_token_create = await self._build_token_pair(user)
        return token_response, refresh_token_create

    async def refresh_access_token(
        self, raw_refresh_token: str
    ) -> Optional[Tuple[str, str, RefreshTokenCreate]]:
        """Exchange a valid refresh token for a new access + refresh pair.

        The old refresh token is revoked (rotation).  Returns None if the
        provided token is invalid, revoked, or expired.
        """
        token_hash = self.hash_token(raw_refresh_token)
        record = await self.refresh_token_repository.get_by_token_hash(token_hash)
        if not record:
            return None

        if record.revoked or record.expires_at < _utc_now():
            return None

        user = await self.user_service.get_user_by_id(record.user_id)
        if not user or not user.is_active:
            return None

        # Revoke old token and issue new pair
        await self.refresh_token_repository.revoke_token(record.id)
        new_access = self.create_access_token(user)
        raw_new_refresh, new_expires = self.create_refresh_token()
        new_refresh_create = RefreshTokenCreate(
            user_id=user.id,
            token_hash=self.hash_token(raw_new_refresh),
            expires_at=new_expires,
            revoked=False,
        )
        return new_access, raw_new_refresh, new_refresh_create

    async def logout(self, raw_refresh_token: str) -> bool:
        """Revoke a single refresh token. Returns True on success."""
        token_hash = self.hash_token(raw_refresh_token)
        return await self.refresh_token_repository.revoke_by_hash(token_hash)

    async def logout_all(self, user_id: str) -> int:
        """Revoke all active refresh tokens for *user_id*."""
        return await self.refresh_token_repository.revoke_user_tokens(user_id)

    async def get_current_user(self, token: str) -> Optional[UserInDB]:
        """Return the user associated with a valid JWT access token."""
        payload = self.verify_access_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return await self.user_service.get_user_by_id(user_id)

    # ------------------------------------------------------------------
    # RBAC helpers
    # ------------------------------------------------------------------

    def has_role(self, user: UserInDB, required_role: UserRole) -> bool:
        """Return True if *user* is allowed to act as *required_role*.

        Hierarchy: admin > doctor > patient.
        """
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.DOCTOR:
            return required_role in (UserRole.DOCTOR, UserRole.PATIENT)
        return user.role == required_role

    def require_role(self, user: UserInDB, required_role: UserRole) -> None:
        """Raise PermissionError when *user* lacks *required_role*."""
        if not self.has_role(user, required_role):
            raise PermissionError(
                f"User role '{user.role.value}' is not permitted to access "
                f"'{required_role.value}' resources"
            )
