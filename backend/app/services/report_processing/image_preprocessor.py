"""
Nura - Image Preprocessor Service
"""

import logging
from typing import Dict, Any
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageStat

logger = logging.getLogger("nura.report_processing.image_preprocessor")


class ImagePreprocessor:
    """Preprocesses images to clean noise and enhance readability before OCR extraction"""

    def preprocess(self, image: Image.Image) -> Dict[str, Any]:
        """Apply preprocessing steps to the input image.
        
        Returns a dict containing:
        - image: preprocessed Image object
        - is_blank: bool (True if the page is blank)
        - details: str message
        """
        try:
            # 1. Orientation correction using EXIF tags
            image = ImageOps.exif_transpose(image)

            # Convert to grayscale to check standard deviation variance for blank page detection
            gray = image.convert("L")
            stat = ImageStat.Stat(gray)
            
            # If standard deviation is extremely low, the page is blank (no variations in color/contrast)
            is_blank = stat.stddev[0] < 5.0
            if is_blank:
                return {
                    "image": image,
                    "is_blank": True,
                    "details": "Blank page detected (stddev variance below threshold)"
                }

            # 2. Contrast Enhancement (increases distinction of characters)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.8)

            # 3. Noise reduction using a Median Filter
            image = image.filter(ImageFilter.MedianFilter(size=3))

            # 4. Resolution normalization
            # OCR engines like Tesseract require high DPI/resolution for correct parsing (typically min 1800px width/height)
            min_dim = 1800
            if image.width < min_dim or image.height < min_dim:
                ratio = min_dim / min(image.width, image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            return {
                "image": image,
                "is_blank": False,
                "details": "Image preprocessed successfully (rotation, contrast, noise, and size normalized)"
            }
        except Exception as exc:
            logger.error(f"Image preprocessing crashed: {exc}", exc_info=True)
            # Safe fallback: return original image
            return {
                "image": image,
                "is_blank": False,
                "details": f"Preprocessing failed, returning raw input: {exc}"
            }
