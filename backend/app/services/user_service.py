"""
Nura - User Service
Business logic for user operations
"""

from typing import Optional
from passlib.context import CryptContext

from app.models import UserCreate, UserUpdate, UserInDB, UserResponse, UserRole, AuthProvider
from app.repositories import UserRepository
from app.services.base import BaseService


# Module-level bcrypt context (created once, thread-safe)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService(BaseService[UserInDB, UserCreate, UserUpdate]):
    """User service — owns all password hashing and user lifecycle logic."""

    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self.user_repository = user_repository

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Return True when *plain_password* matches *hashed_password*."""
        return _pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """Return a bcrypt hash of *password*."""
        return _pwd_context.hash(password)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_user(self, user_create: UserCreate) -> UserInDB:
        """Create a new user.  Raises ValueError if the email is taken."""
        email = user_create.email.lower().strip()

        if await self.user_repository.exists_by_email(email):
            raise ValueError(f"User with email {email} already exists")

        # Build a plain dict so we can swap *password* for *password_hash*
        user_data = user_create.model_dump(exclude={"password"})
        user_data["password_hash"] = self.hash_password(user_create.password)
        user_data["email"] = email
        user_data.setdefault("role", UserRole.PATIENT)
        user_data.setdefault("auth_provider", AuthProvider.LOCAL)
        user_data.setdefault("email_verified", False)
        user_data.setdefault("is_active", True)

        # Insert raw dict via the base repository so we don't need a password field
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        user_data.setdefault("created_at", now)
        user_data.setdefault("updated_at", now)

        result = await self.user_repository.collection.insert_one(user_data)
        created_doc = await self.user_repository.collection.find_one({"_id": result.inserted_id})
        if created_doc is None:
            raise RuntimeError("User was inserted but could not be retrieved")
        return UserInDB.from_mongo(created_doc)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        return await self.user_repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        return await self.user_repository.get_by_email(email)

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[UserInDB]:
        return await self.user_repository.update(user_id, user_update)

    async def verify_user_email(self, user_id: str) -> Optional[UserInDB]:
        return await self.user_repository.verify_email(user_id)

    async def user_exists(self, email: str) -> bool:
        return await self.user_repository.exists_by_email(email)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Return the user if credentials are valid, else None."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    # ------------------------------------------------------------------
    # Password management
    # ------------------------------------------------------------------

    async def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        """Change password after verifying the old one.  Returns False on mismatch."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        if not self.verify_password(old_password, user.password_hash):
            return False

        # Reuse the Pydantic validator for strength checks
        UserCreate.validate_password(new_password)

        result = await self.user_repository.update(
            user_id, UserUpdate(password_hash=self.hash_password(new_password))  # type: ignore[call-arg]
        )
        return result is not None

    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """Unconditionally reset a user's password (forgot-password flow)."""
        if not await self.get_user_by_id(user_id):
            return False

        UserCreate.validate_password(new_password)

        result = await self.user_repository.update(
            user_id, UserUpdate(password_hash=self.hash_password(new_password))  # type: ignore[call-arg]
        )
        return result is not None

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_response(self, user: UserInDB) -> UserResponse:
        """Convert a UserInDB to a UserResponse (strips the password hash)."""
        return UserResponse(
            id=user.id,
            role=user.role,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            profile_picture=user.profile_picture,
            auth_provider=user.auth_provider,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
