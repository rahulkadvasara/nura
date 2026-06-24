"""
Nura - Refresh Token Model
MongoDB model for JWT refresh tokens
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class RefreshTokenBase(BaseModel):
    """Base refresh token model"""
    user_id: str = Field(..., description="User ID")
    token_hash: str = Field(..., description="Hashed refresh token")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    revoked: bool = Field(default=False, description="Token revocation status")
    last_activity: datetime = Field(default_factory=utc_now, description="Last activity timestamp")



class RefreshTokenCreate(RefreshTokenBase):
    """Refresh token creation model"""
    pass


class RefreshTokenInDB(RefreshTokenBase):
    """Refresh token model as stored in database"""
    id: str = Field(..., description="Token ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "RefreshTokenInDB":
        """Create RefreshTokenInDB from a raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)


class RefreshTokenResponse(BaseModel):
    """Refresh token response model"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

    id: str = Field(..., description="Token ID")
    user_id: str = Field(..., description="User ID")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    revoked: bool = Field(..., description="Token revocation status")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")

