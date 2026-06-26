"""
Nura - Content Hashing Utilities
Generates deterministic hashes for document verification and index updates
"""

import hashlib


def generate_content_hash(content: str) -> str:
    """
    Generate a deterministic SHA-256 hash string for a text segment.
    
    Args:
        content: String text content to hash.
        
    Returns:
        Hexadecimal SHA-256 string representation of the hash.
    """
    if content is None:
        content = ""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
