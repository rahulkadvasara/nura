"""
Nura - Qdrant Vector Database Connection Manager
"""

from typing import Optional
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models
except ImportError:  # pragma: no cover
    # Provide minimal stub classes to allow imports without the actual package
    class QdrantClient:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Qdrant client is not installed. Install 'qdrant-client' to use this feature.")

    class _DummyModels:
        class VectorParams:
            def __init__(self, *args, **kwargs):
                pass

        class Distance:
            COSINE = "COSINE"

    qdrant_models = _DummyModels
import logging

from app.core.config import settings
from app.core.constants import QDRANT_COLLECTIONS

logger = logging.getLogger(__name__)


class QdrantConnection:
    """Qdrant connection manager"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
    
    async def connect(self) -> None:
        """Create Qdrant connection"""
        try:
            # Handle empty API key for development
            api_key = settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=api_key,
                timeout=30.0
            )
            
            # Test connection
            collections = self.client.get_collections()
            
            logger.info("Qdrant connected successfully", extra={
                "collections_count": len(collections.collections)
            })
            
            # Initialize collections if they don't exist
            await self._initialize_collections()
            
        except Exception as e:
            logger.warning(f"Qdrant connection failed (this is OK for Phase 0): {e}")
            # For Phase 0, we'll allow this to fail gracefully
            self.client = None
    
    async def close(self) -> None:
        """Close Qdrant connection"""
        if self.client:
            self.client.close()
            logger.info("Qdrant connection closed")
    
    async def is_connected(self) -> bool:
        """Check if Qdrant is connected"""
        try:
            if self.client:
                self.client.get_collections()
                return True
            return False
        except Exception:
            return False
    
    def get_client(self) -> QdrantClient:
        """Get Qdrant client instance"""
        if not self.client:
            raise RuntimeError("Qdrant not connected")
        return self.client
    
    async def _initialize_collections(self) -> None:
        """Initialize Qdrant collections if they don't exist"""
        try:
            existing_collections = self.client.get_collections()
            existing_names = {col.name for col in existing_collections.collections}
            
            # Collection configurations
            collections_config = {
                QDRANT_COLLECTIONS["PATIENT_REPORTS"]: {
                    "vectors_config": qdrant_models.VectorParams(
                        size=384,  # BAAI/bge-small-en-v1.5 dimension
                        distance=qdrant_models.Distance.COSINE
                    )
                },
                QDRANT_COLLECTIONS["CHAT_MEMORY"]: {
                    "vectors_config": qdrant_models.VectorParams(
                        size=384,
                        distance=qdrant_models.Distance.COSINE
                    )
                },
                QDRANT_COLLECTIONS["MEDICAL_KNOWLEDGE"]: {
                    "vectors_config": qdrant_models.VectorParams(
                        size=384,
                        distance=qdrant_models.Distance.COSINE
                    )
                },
                QDRANT_COLLECTIONS["DRUG_INTERACTIONS"]: {
                    "vectors_config": qdrant_models.VectorParams(
                        size=384,
                        distance=qdrant_models.Distance.COSINE
                    )
                },
                QDRANT_COLLECTIONS["DOCTOR_KNOWLEDGE"]: {
                    "vectors_config": qdrant_models.VectorParams(
                        size=384,
                        distance=qdrant_models.Distance.COSINE
                    )
                }
            }
            
            # Create missing collections
            for collection_name, config in collections_config.items():
                if collection_name not in existing_names:
                    self.client.create_collection(
                        collection_name=collection_name,
                        **config
                    )
                    logger.info(f"Created Qdrant collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collections: {e}")
            raise


# Global Qdrant connection instance
qdrant_connection = QdrantConnection()


async def connect_to_qdrant() -> None:
    """Connect to Qdrant"""
    await qdrant_connection.connect()


async def close_qdrant_connection() -> None:
    """Close Qdrant connection"""
    await qdrant_connection.close()


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance"""
    return qdrant_connection.get_client()


async def get_qdrant_status() -> str:
    """Get Qdrant connection status"""
    try:
        is_connected = await qdrant_connection.is_connected()
        return "connected" if is_connected else "not_configured"
    except Exception:
        return "not_configured"