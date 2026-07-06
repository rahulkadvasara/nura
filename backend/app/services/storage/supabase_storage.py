import io
import os
import logging
from typing import BinaryIO, Optional, Dict, Any
from supabase import create_client, Client
from app.services.storage.storage_provider import StorageProvider
from app.core.config import settings

logger = logging.getLogger("nura.storage.supabase")

class SupabaseStorage(StorageProvider):
    """Supabase Storage implementation using the official supabase Python SDK."""

    def __init__(self):
        url = settings.SUPABASE_URL
        # Prioritize service role key for admin upload/delete capabilities, fallback to anon
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        
        if not url:
            raise ValueError("SUPABASE_URL is not configured")
        if not key:
            raise ValueError("SUPABASE key (service role or anon) is not configured")

        # Sanitize URL by removing rest subpath and trailing slashes
        if "/rest/v1" in url:
            url = url.split("/rest/v1")[0]
        url = url.rstrip("/")

        self.client: Client = create_client(url, key)

    def _ensure_bucket(self, bucket_name: str) -> None:
        """Helper to ensure target bucket exists and is publicly accessible."""
        try:
            buckets = self.client.storage.list_buckets()
            bucket_names = []
            for b in buckets:
                if hasattr(b, "name"):
                    bucket_names.append(b.name)
                elif isinstance(b, dict) and "name" in b:
                    bucket_names.append(b["name"])
            
            if bucket_name not in bucket_names:
                logger.info(f"Creating missing Supabase bucket: {bucket_name}")
                self.client.storage.create_bucket(bucket_name, options={"public": True})
        except Exception as e:
            logger.warning(f"Failed to verify/create bucket {bucket_name}: {e}")

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        bucket: str,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        # Clean bucket name (ensure standard formatting)
        bucket = bucket.lower().replace("_", "-")
        self._ensure_bucket(bucket)

        try:
            file.seek(0)
        except Exception:
            pass

        file_bytes = file.read()
        size = len(file_bytes)

        # Upload options
        file_options = {}
        if content_type:
            file_options["content-type"] = content_type

        # Perform upload using postgrest/storage SDK
        # We target filename as the path key on Supabase bucket
        res = self.client.storage.from_(bucket).upload(
            path=filename,
            file=file_bytes,
            file_options=file_options
        )

        public_url = self.get_public_url(bucket, filename)

        return {
            "provider": "supabase",
            "bucket": bucket,
            "object_key": filename,
            "public_url": public_url,
            "content_type": content_type or "application/octet-stream",
            "size": size
        }

    async def delete_file(self, bucket: str, object_key: str) -> bool:
        bucket = bucket.lower().replace("_", "-")
        try:
            # remove takes a list of paths
            res = self.client.storage.from_(bucket).remove([object_key])
            # If the response contains list and it is not empty, it was deleted
            if res and isinstance(res, list) and len(res) > 0:
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {object_key} from bucket {bucket}: {e}")
            return False

    def get_public_url(self, bucket: str, object_key: str) -> str:
        bucket = bucket.lower().replace("_", "-")
        return self.client.storage.from_(bucket).get_public_url(object_key)

    async def exists(self, bucket: str, object_key: str) -> bool:
        bucket = bucket.lower().replace("_", "-")
        try:
            # Search by directory/basename
            dir_name = os.path.dirname(object_key) or ""
            base_name = os.path.basename(object_key)
            
            res = self.client.storage.from_(bucket).list(path=dir_name)
            for item in res:
                if isinstance(item, dict) and item.get("name") == base_name:
                    return True
            return False
        except Exception:
            return False
