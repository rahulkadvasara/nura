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
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        bucket_dir = os.path.join(self.base_dir, bucket)
        os.makedirs(bucket_dir, exist_ok=True)
        filepath = os.path.join(bucket_dir, filename)

        # Handle seeking if needed
        try:
            file.seek(0)
        except Exception:
            pass

        content = file.read()
        size = len(content)

        with open(filepath, "wb") as buffer:
            buffer.write(content)

        object_key = filename
        public_url = f"{self.base_url}uploads/{bucket}/{filename}"

        return {
            "provider": "local",
            "bucket": bucket,
            "object_key": object_key,
            "public_url": public_url,
            "content_type": content_type or "application/octet-stream",
            "size": size
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
