"""
Nura - PDF Extractor Service
"""

import io
import logging
from typing import List, Dict, Any
from pypdf import PdfReader

logger = logging.getLogger("nura.report_processing.pdf_extractor")


class PDFExtractor:
    """Extracts direct text from digital PDFs, page-by-page"""

    async def extract_text(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract text from all pages in the PDF.
        
        Returns a list of dicts with:
        - page_number: int (1-based)
        - text: str
        - is_scanned: bool (true if text character count < 50)
        """
        pages = []
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            for i, page in enumerate(reader.pages):
                text = ""
                try:
                    text = page.extract_text() or ""
                except Exception as page_exc:
                    logger.warning(f"Failed to extract text from page {i + 1}: {page_exc}")
                
                # Check if page is scanned/needs OCR (char count < 50)
                is_scanned = len(text.strip()) < 50
                
                pages.append({
                    "page_number": i + 1,
                    "text": text,
                    "is_scanned": is_scanned
                })
        except Exception as exc:
            logger.error(f"Failed to parse PDF document bytes: {exc}", exc_info=True)
            raise ValueError(f"Invalid PDF document format: {exc}")

        return pages
