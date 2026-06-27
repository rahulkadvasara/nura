import pytest
from PIL import Image
from app.services.report_processing.image_preprocessor import ImagePreprocessor
from app.services.report_processing.ocr_service import OCRService


def test_image_preprocessor_blank():
    preprocessor = ImagePreprocessor()
    
    # Create blank grayscale image
    img = Image.new("L", (100, 100), color=255)
    res = preprocessor.preprocess(img)
    
    assert res["is_blank"] is True
    assert "Blank page" in res["details"]


@pytest.mark.asyncio
async def test_ocr_service_fallback():
    ocr = OCRService()
    
    # Create dummy image
    img = Image.new("RGB", (200, 200), color=(255, 0, 0))
    res = await ocr.perform_ocr(img)
    
    assert "text" in res
    assert res["confidence"] > 0.0
    assert res["method"] in ("tesseract", "simulated_ocr")
