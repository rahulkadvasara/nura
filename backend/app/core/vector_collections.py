"""
Nura - Vector Collections Mappings
"""
from typing import Dict
from app.core.constants import QDRANT_COLLECTIONS

# Document type to Qdrant collection mapping
DOCUMENT_COLLECTION_MAP: Dict[str, str] = {
    "REPORT": QDRANT_COLLECTIONS["PATIENT_REPORTS"],
    "MEDICAL_ARTICLE": QDRANT_COLLECTIONS["MEDICAL_KNOWLEDGE"],
    "DRUG_DATASET": QDRANT_COLLECTIONS["DRUG_KNOWLEDGE"],
    "DOCTOR_PROFILE": QDRANT_COLLECTIONS["DOCTOR_KNOWLEDGE"],
    "CHAT_MEMORY": QDRANT_COLLECTIONS["CHAT_MEMORY"]
}


def get_collection_for_document_type(document_type: str) -> str:
    """
    Retrieve Qdrant collection name for a given document type.
    
    Args:
        document_type: Upper/Lowercase string (e.g. REPORT, MEDICAL_ARTICLE)
        
    Returns:
        Collection name mapped in QDRANT_COLLECTIONS
    """
    doc_type_upper = document_type.upper().strip()
    if doc_type_upper not in DOCUMENT_COLLECTION_MAP:
        raise ValueError(f"Unsupported document type mapping target: '{document_type}'")
    return DOCUMENT_COLLECTION_MAP[doc_type_upper]
