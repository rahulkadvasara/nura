import os
from typing import BinaryIO, Optional, Dict, Any
from app.services.storage.storage_provider import StorageProvider
from app.core.config import settings

class LocalStorage(StorageProvider):
    """Local filesystem storage implementation."""

    def __init__(self, base_dir: str = "uploads", base_url: Optional[str] = None):
        self.base_dir = base_dir
        self.base_url = (base_url or settings.BACKEND_URL).rstrip("/") + "/"

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        bucket: str,
        content_type: Optional[str] = None,
        original_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        import hashlib
        from datetime import datetime, timezone

        # Ensure correct bucket directory exists
        bucket_dir = os.path.join(self.base_dir, bucket)
        filepath = os.path.join(bucket_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Handle seeking if needed
        try:
            file.seek(0)
        except Exception:
            pass

        content = file.read()
        size_bytes = len(content)

        with open(filepath, "wb") as buffer:
            buffer.write(content)

        # Calculate SHA-256 checksum
        sha = hashlib.sha256()
        sha.update(content)
        checksum_sha256 = sha.hexdigest()

        # Build public url only for avatars bucket, private files use signed urls
        is_public = (bucket == "avatars")
        public_url = self.get_public_url(bucket, filename) if is_public else None
        
        orig_name = original_filename or os.path.basename(filename)

        return {
            "provider": "local",
            "bucket": bucket,
            "object_key": filename,
            "public_url": public_url,
            "original_filename": orig_name,
            "content_type": content_type or "application/octet-stream",
            "size_bytes": size_bytes,
            "checksum_sha256": checksum_sha256,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "storage_version": "1.0.0"
        }

    async def delete_file(self, bucket: str, object_key: str) -> bool:
        filepath = os.path.join(self.base_dir, bucket, object_key)
        if os.path.exists(filepath) and os.path.isfile(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception:
                return False
        return False

    def get_public_url(self, bucket: str, object_key: str) -> str:
        return f"{self.base_url}uploads/{bucket}/{object_key}"

    async def exists(self, bucket: str, object_key: str) -> bool:
        filepath = os.path.join(self.base_dir, bucket, object_key)
        return os.path.exists(filepath) and os.path.isfile(filepath)

    def generate_signed_url(self, bucket: str, object_key: str, expires_in: int = 3600) -> str:
        return self.get_public_url(bucket, object_key)
