"""
Nura - Document Metadata Builder Service
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.core.ai_config import AISettings, ai_settings
from app.utils.hash import generate_content_hash
from app.services.index_version_service import IndexVersionService, get_index_version_service


class DocumentMetadataService:
    """Service responsible for generating standardized metadata payloads for document vectors"""

    def __init__(self, version_service: IndexVersionService, settings: AISettings = ai_settings):
        self.version_service = version_service
        self.settings = settings

    def build_metadata(
        self,
        document_id: str,
        document_type: str,
        chunk_index: int,
        content: str,
        patient_id: Optional[str] = None,
        report_id: Optional[str] = None,
        page_number: Optional[int] = 1,
        section: Optional[str] = "content",
        source: Optional[str] = "mongodb",
        language: Optional[str] = "en",
        created_by: Optional[str] = "system"
    ) -> Dict[str, Any]:
        """
        Build standardized metadata payload dictionary.
        
        Args:
            document_id: MongoDB ID of the parent document
            document_type: String category (e.g. REPORT, MEDICAL_ARTICLE)
            chunk_index: Zero-based integer index of the chunk
            content: Raw text content of the chunk segment
            patient_id: Link to Patient ID if patient-specific
            report_id: Link to Report ID if a report document
            page_number: Location page number (default 1)
            section: Section label (default 'content')
            source: Source system identifier (default 'mongodb')
            language: Locale label (default 'en')
            created_by: ID/label of the creating user (default 'system')
            
        Returns:
            Dict containing all 16 standardized metadata fields
        """
        # Calculate SHA256 content hash of the chunk
        content_hash = generate_content_hash(content)
        
        # Unique chunk ID (e.g., doc_123_chunk_0)
        chunk_id = f"{document_id}_chunk_{chunk_index}"
        
        return {
            "patient_id": patient_id,
            "report_id": report_id,
            "document_id": document_id,
            "document_type": document_type.upper().strip(),
            "chunk_id": chunk_id,
            "chunk_index": chunk_index,
            "page_number": page_number if page_number is not None else 1,
            "section": section if section else "content",
            "source": source if source else "mongodb",
            "language": language if language else "en",
            "created_by": created_by if created_by else "system",
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "embedding_model": self.settings.EMBEDDING_MODEL,
            "embedding_version": self.version_service.get_embedding_version(),
            "content": content,
            "content_hash": content_hash,
            "index_version": self.version_service.get_index_version()
        }


# Singleton reference helper
_document_metadata_service_instance = None


def get_document_metadata_service() -> DocumentMetadataService:
    """Retrieve singleton instance of DocumentMetadataService"""
    global _document_metadata_service_instance
    if _document_metadata_service_instance is None:
        version_svc = get_index_version_service()
        _document_metadata_service_instance = DocumentMetadataService(
            version_service=version_svc,
            settings=ai_settings
        )
    return _document_metadata_service_instance
