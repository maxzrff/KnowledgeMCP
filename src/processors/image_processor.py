"""
Image document processor.
"""

from pathlib import Path
from typing import Any

from PIL import Image

from src.models.document import DocumentFormat, ProcessingMethod
from src.processors.base import BaseProcessor
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ImageProcessor(BaseProcessor):
    """Image document processor (requires OCR)."""

    def __init__(self, supported_format: DocumentFormat):
        self._format = supported_format

    @property
    def supported_format(self) -> DocumentFormat:
        return self._format

    async def extract_text(self, file_path: Path) -> str:
        """Extract text from image (placeholder for OCR)."""
        # This will be handled by OCR service
        return ""

    async def extract_metadata(self, file_path: Path) -> dict[str, Any]:
        """Extract metadata from image."""
        try:
            with Image.open(file_path) as img:
                metadata = {
                    "format": self._format.value,
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                }

                # Extract EXIF data if available
                if hasattr(img, "_getexif") and img._getexif():
                    exif = img._getexif()
                    if exif:
                        metadata["exif"] = {k: str(v) for k, v in exif.items()}

                return metadata
        except Exception as e:
            logger.warning(f"Failed to extract image metadata: {e}")
            return {"format": self._format.value}

    async def process(self, file_path: Path) -> tuple[str, dict[str, Any], ProcessingMethod]:
        """Process image - requires OCR or image analysis."""
        metadata = await self.extract_metadata(file_path)
        return "", metadata, ProcessingMethod.IMAGE_ANALYSIS
