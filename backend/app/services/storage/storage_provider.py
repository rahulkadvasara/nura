from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, Dict, Any

class StorageProvider(ABC):
    """Abstract interface defining required storage operations."""

    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        bucket: str,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Uploads a file to the storage backend.
        
        Args:
            file: File-like binary stream.
            filename: Target file name.
            bucket: Name of the bucket.
            content_type: MIME type of the file.

        Returns:
            Dict containing metadata:
                - provider (str)
                - bucket (str)
                - object_key (str)
                - public_url (str)
                - content_type (str)
                - size (int)
        """
        pass

    @abstractmethod
    async def delete_file(self, bucket: str, object_key: str) -> bool:
        """Deletes a file from the storage backend.
        
        Args:
            bucket: Name of the bucket.
            object_key: Key or path of the object on the storage.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_public_url(self, bucket: str, object_key: str) -> str:
        """Retrieves the public URL for a given file.
        
        Args:
            bucket: Name of the bucket.
            object_key: Key or path of the object on the storage.

        Returns:
            str: Public accessible URL.
        """
        pass

    @abstractmethod
    async def exists(self, bucket: str, object_key: str) -> bool:
        """Checks if a file exists in the storage backend.
        
        Args:
            bucket: Name of the bucket.
            object_key: Key or path of the object.

        Returns:
            bool: True if file exists, False otherwise.
        """
        pass
