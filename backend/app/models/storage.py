from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)

class FileMetadata(BaseModel):
    """Reusable model for rich file metadata stored in MongoDB collections."""
    provider: str = Field(..., description="Storage provider name (e.g., 'local', 'supabase')")
    bucket: str = Field(..., description="Name of the storage bucket")
    object_key: str = Field(..., description="Relative path/object key inside the bucket")
    public_url: Optional[str] = Field(None, description="Public access URL (null for private documents)")
    original_filename: str = Field(..., description="Original filename before upload and clean")
    content_type: str = Field(..., description="MIME content type (e.g., 'application/pdf')")
    size_bytes: int = Field(..., description="File size in bytes")
    checksum_sha256: str = Field(..., description="SHA-256 checksum of the file content")
    uploaded_at: datetime = Field(default_factory=utc_now, description="Timestamp when the file was uploaded")
    last_accessed_at: Optional[datetime] = Field(None, description="Timestamp of last access")
    storage_version: str = Field(default="1.0.0", description="Version identifier of this storage schema")
