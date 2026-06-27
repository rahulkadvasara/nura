import pytest
from app.services.report_processing.pdf_extractor import PDFExtractor


@pytest.mark.asyncio
async def test_pdf_extractor_scanned_check():
    extractor = PDFExtractor()
    
    # Check invalid PDF bytes raises ValueError
    with pytest.raises(ValueError):
        await extractor.extract_text(b"corrupted pdf bytes")
