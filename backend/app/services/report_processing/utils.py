"""
Nura - Report Processing Utility Functions
"""

import re
from typing import Optional


def detect_file_type(file_bytes: bytes) -> Optional[str]:
    """Detect file type based on file magic bytes.
    
    Supports: pdf, png, jpeg/jpg.
    Returns file extension or None if unsupported.
    """
    if not file_bytes or len(file_bytes) < 4:
        return None

    # Check PDF magic bytes (%PDF)
    if file_bytes[:4] == b"%PDF":
        return "pdf"

    # Check PNG magic bytes
    if file_bytes[:4] == b"\x89PNG":
        return "png"

    # Check JPEG/JPG magic bytes (FF D8 FF)
    if file_bytes[:3] == b"\xff\xd8\xff":
        return "jpeg"

    return None


def normalize_text_content(text: str) -> str:
    """Normalize text extracted from report documents.
    
    Cleans multiple spaces, normalizes line ends, and formats margins.
    """
    if not text:
        return ""

    # Replace windows line endings
    text = text.replace("\r\n", "\n")

    # Replace multiple spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize double newlines or more to double newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip empty spaces on line boundaries
    lines = [line.strip() for line in text.split("\n")]
    
    # Filter out empty lines that stack
    normalized = "\n".join(lines)
    
    # Final trim
    return normalized.strip()
