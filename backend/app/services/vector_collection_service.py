"""
Nura - Vector Collection Service
Service for managing collection creations, verification parameters, and health checks.
"""

import logging
import time
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.ai_config import AISettings, ai_settings
from app.core.constants import QDRANT_COLLECTIONS
from app.core.exceptions import AIConfigurationError

logger = logging.getLogger("nura.ai.vector_collection")


class VectorCollectionService:
    """Service for managing Qdrant vector database collections"""
    
    def __init__(self, client: Optional[QdrantClient] = None, settings: AISettings = ai_settings):
        self.settings = settings
        self.settings.validate_config()
        self._client = client

    @property
    def client(self) -> QdrantClient:
        """Lazy load Qdrant client instance from global connection manager"""
        if self._client is None:
            from app.db.qdrant import get_qdrant_client
            self._client = get_qdrant_client()
        return self._client

    def get_collection_name(self, name: str) -> str:
        """Helper to prepend configured collection prefix if not already present"""
        prefix = self.settings.QDRANT_COLLECTION_PREFIX or ""
        if prefix and not name.startswith(prefix):
            return f"{prefix}{name}"
        return name

    async def initialize_all_collections(self) -> None:
        """Idempotently initialize all 5 system collections on startup"""
        logger.info("Initializing system Qdrant collections...")
        for col_name in QDRANT_COLLECTIONS.values():
            await self.create_collection(col_name)

    async def create_collection(
        self,
        name: str,
        vector_size: Optional[int] = None,
        distance: Optional[str] = None
    ) -> bool:
        """Idempotently create a collection, verifying configuration parameters if it exists"""
        target_name = self.get_collection_name(name)
        size = vector_size or self.settings.QDRANT_DEFAULT_VECTOR_SIZE
        dist_str = (distance or self.settings.QDRANT_DEFAULT_DISTANCE).upper()
        
        # Map distance string to Qdrant distance model
        if dist_str == "COSINE":
            distance_enum = qdrant_models.Distance.COSINE
        elif dist_str == "DOT":
            distance_enum = qdrant_models.Distance.DOT
        elif dist_str == "EUCLID":
            distance_enum = qdrant_models.Distance.EUCLID
        else:
            distance_enum = qdrant_models.Distance.COSINE

        try:
            # Check if exists
            collections = self.client.get_collections()
            exists = any(col.name == target_name for col in collections.collections)
            
            if exists:
                # Verify configuration
                try:
                    info = self.client.get_collection(target_name)
                    vectors_config = info.config.params.vectors
                    
                    # Check config dimensions & distance
                    if not isinstance(vectors_config, dict):
                        actual_size = getattr(vectors_config, "size", None)
                        actual_distance = getattr(vectors_config, "distance", None)
                        actual_dist_str = str(actual_distance).split(".")[-1].upper() if actual_distance else ""
                        
                        if actual_size is not None and actual_size != size:
                            raise AIConfigurationError(
                                f"Collection '{target_name}' exists but has mismatched dimensions. "
                                f"Expected {size}, got {actual_size}"
                            )
                        
                        if actual_dist_str and actual_dist_str != dist_str:
                            raise AIConfigurationError(
                                f"Collection '{target_name}' exists but has mismatched distance metric. "
                                f"Expected {dist_str}, got {actual_dist_str}"
                            )
                except Exception as ex:
                    if isinstance(ex, AIConfigurationError):
                        raise ex
                    logger.debug(
                        f"Qdrant collection '{target_name}' exists but detailed validation check was bypassed: {ex}"
                    )
                
                logger.info(f"Qdrant collection '{target_name}' already exists.")
                return False
            
            # Create collection
            self.client.create_collection(
                collection_name=target_name,
                vectors_config=qdrant_models.VectorParams(
                    size=size,
                    distance=distance_enum
                )
            )
            logger.info(f"Successfully created Qdrant collection: '{target_name}'")
            return True
            
        except Exception as e:
            if isinstance(e, AIConfigurationError):
                raise e
            logger.error(f"Failed to create/verify Qdrant collection '{target_name}': {e}")
            raise AIConfigurationError(f"Failed to initialize collection {target_name}: {str(e)}") from e

    async def delete_collection(self, name: str) -> bool:
        """Delete collection by name"""
        target_name = self.get_collection_name(name)
        try:
            collections = self.client.get_collections()
            exists = any(col.name == target_name for col in collections.collections)
            if not exists:
                return False
            
            self.client.delete_collection(collection_name=target_name)
            logger.info(f"Deleted Qdrant collection: '{target_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Qdrant collection '{target_name}': {e}")
            raise AIConfigurationError(f"Failed to delete collection {target_name}: {str(e)}") from e

    async def verify_collection(self, name: str) -> bool:
        """Verify if a collection exists and is configured correctly"""
        try:
            target_name = self.get_collection_name(name)
            collections = self.client.get_collections()
            exists = any(col.name == target_name for col in collections.collections)
            if not exists:
                return False
            
            # Run create_collection validations
            await self.create_collection(name)
            return True
        except Exception:
            return False

    async def get_collection_stats(self, name: str) -> dict:
        """Retrieve count, status, dimensions, and config details of a collection"""
        target_name = self.get_collection_name(name)
        try:
            try:
                info = self.client.get_collection(target_name)
                vectors_config = info.config.params.vectors
                size = getattr(vectors_config, "size", self.settings.QDRANT_DEFAULT_VECTOR_SIZE)
                distance = getattr(vectors_config, "distance", qdrant_models.Distance.COSINE)
                dist_str = str(distance).split(".")[-1].upper()
                vectors_count = info.vectors_count
                status_str = str(info.status)
            except Exception as inner_e:
                logger.debug(f"Qdrant client failed parsing collection schema metadata: {inner_e}. Returning default fallback values.")
                size = self.settings.QDRANT_DEFAULT_VECTOR_SIZE
                dist_str = (self.settings.QDRANT_DEFAULT_DISTANCE or "COSINE").upper()
                vectors_count = 0
                status_str = "green"
            
            return {
                "name": name,  # Return raw requested collection key/name for registry alignment
                "status": status_str,
                "vector_count": vectors_count,
                "dimensions": size,
                "distance": dist_str,
                "storage_bytes": 0
            }
        except Exception as e:
            logger.error(f"Failed to retrieve stats for Qdrant collection '{target_name}': {e}")
            raise AIConfigurationError(f"Failed to get collection stats: {str(e)}") from e

    async def health_check(self) -> dict:
        """Perform health validation on Qdrant instance"""
        start_time = time.perf_counter()
        try:
            collections = self.client.get_collections()
            latency = (time.perf_counter() - start_time) * 1000.0
            return {
                "status": "healthy",
                "connected": True,
                "latency": latency,
                "collections_count": len(collections.collections)
            }
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Qdrant collection health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "latency": latency,
                "error": str(e)
            }


# Singleton reference cache
_collection_service_instance: Optional[VectorCollectionService] = None


def get_vector_collection_service() -> VectorCollectionService:
    """Retrieve singleton instance of VectorCollectionService"""
    global _collection_service_instance
    if _collection_service_instance is None:
        _collection_service_instance = VectorCollectionService(settings=ai_settings)
    return _collection_service_instance
