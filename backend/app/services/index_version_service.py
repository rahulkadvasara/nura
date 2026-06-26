"""
Nura - Index Version Manager Service
Handles version tracking for embeddings, index structures, and collection schemas.
"""
import logging
from typing import Dict, Any
from app.core.ai_config import AISettings, ai_settings

logger = logging.getLogger("nura.ai.version")


class IndexVersionService:
    """Service to track, audit, and manage active schemas and indexing versions"""

    def __init__(self, settings: AISettings = ai_settings):
        self.settings = settings

    def get_embedding_version(self) -> str:
        """Get active embedding scheme version (e.g. 'v1')"""
        return self.settings.EMBEDDING_VERSION

    def get_index_version(self) -> int:
        """Get active index structural format version (e.g. 3)"""
        return self.settings.INDEX_VERSION

    def get_schema_version(self) -> int:
        """Get active collection DB schema layout version (e.g. 2)"""
        return self.settings.SCHEMA_VERSION

    def get_collection_version(self) -> str:
        """Compile consolidated configuration version string"""
        return f"{self.get_embedding_version()}_i{self.get_index_version()}_s{self.get_schema_version()}"

    def is_compatible(self, metadata_payload: Dict[str, Any]) -> bool:
        """
        Check if the parsed vector chunk metadata matches the current platform versions.
        
        Args:
            metadata_payload: Dictionary payload from vector point
            
        Returns:
            True if embedding_version and index_version match current settings, False otherwise.
        """
        point_emb_version = metadata_payload.get("embedding_version")
        point_idx_version = metadata_payload.get("index_version")
        
        # Exact compatibility constraint matching
        emb_match = point_emb_version == self.get_embedding_version()
        idx_match = point_idx_version == self.get_index_version()
        
        return bool(emb_match and idx_match)


# Singleton reference helper
_index_version_service_instance = None


def get_index_version_service() -> IndexVersionService:
    """Retrieve singleton instance of IndexVersionService"""
    global _index_version_service_instance
    if _index_version_service_instance is None:
        _index_version_service_instance = IndexVersionService(settings=ai_settings)
    return _index_version_service_instance
