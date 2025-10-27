"""
OCR service using Tesseract with smart detection and PDF processing.
"""

import asyncio
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class OCRService:
    """Service for OCR processing using Tesseract with smart detection."""

    def __init__(
        self,
        language: str = "eng",
        force_ocr: bool = False,
        max_workers: int = 2
    ):
        """
        Initialize OCR service.

        Args:
            language: OCR language code (default: "eng")
            force_ocr: Always use OCR regardless of text quality
            max_workers: Number of worker threads for OCR processing
        """
        self.language = language
        self.force_ocr = force_ocr
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract OCR not available - install pytesseract and tesseract-ocr")
        
        if not PDF2IMAGE_AVAILABLE:
            logger.warning("pdf2image not available - install pdf2image for PDF OCR support")

    async def is_ocr_needed(self, extracted_text: str) -> bool:
        """
        Determine if OCR is needed based on extracted text quality.

        Args:
            extracted_text: Text extracted from document

        Returns:
            True if OCR is recommended
        """
        if self.force_ocr:
            logger.info("Force OCR enabled - OCR will be used")
            return True

        text_length = len(extracted_text.strip())

        # Too little text suggests scanned document
        if text_length < 100:
            logger.info(f"Text too short ({text_length} chars) - OCR recommended")
            return True

        # Check for gibberish (high ratio of non-alphanumeric characters)
        alphanumeric = sum(c.isalnum() or c.isspace() for c in extracted_text)
        ratio = alphanumeric / len(extracted_text) if extracted_text else 0

        if ratio < 0.7:  # Less than 70% readable characters
            logger.info(f"Low alphanumeric ratio ({ratio:.2%}) - OCR recommended")
            return True

        logger.info("Text quality sufficient - OCR not needed")
        return False

    async def extract_text_from_image(
        self,
        image_path: Path,
        language: Optional[str] = None,
    ) -> tuple[str, float]:
        """
        Extract text from image using OCR.

        Args:
            image_path: Path to image file
            language: OCR language code (uses instance default if None)

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract OCR not available")

        lang = language or self.language

        try:
            # Run OCR in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text, confidence = await loop.run_in_executor(
                self.executor,
                self._extract_text_sync,
                image_path,
                lang
            )

            logger.info(
                f"OCR extracted {len(text)} characters from {image_path.name} "
                f"(confidence: {confidence:.2f})"
            )

            return text, confidence
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            raise

    def _extract_text_sync(self, image_path: Path, language: str) -> tuple[str, float]:
        """Synchronous OCR extraction (runs in thread pool)."""
        # Load and preprocess image
        image = Image.open(image_path)

        # Convert to grayscale for better OCR
        if image.mode != "L":
            image = image.convert("L")

        # Extract text
        text = pytesseract.image_to_string(image, lang=language)

        # Get confidence score
        data = pytesseract.image_to_data(
            image, lang=language, output_type=pytesseract.Output.DICT
        )
        confidences = [int(conf) for conf in data["conf"] if conf != "-1"]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        confidence_score = avg_confidence / 100.0  # Normalize to 0-1

        return text, confidence_score

    async def process_pdf_with_ocr(
        self,
        pdf_path: Path,
        language: Optional[str] = None,
    ) -> tuple[str, float]:
        """
        Extract text from PDF using OCR by converting pages to images.

        Args:
            pdf_path: Path to PDF file
            language: OCR language code (uses instance default if None)

        Returns:
            Tuple of (combined_text, average_confidence)
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract OCR not available")
        
        if not PDF2IMAGE_AVAILABLE:
            raise RuntimeError("pdf2image not available - install pdf2image for PDF OCR")

        lang = language or self.language
        temp_dir = None

        try:
            # Create temporary directory for images
            temp_dir = tempfile.TemporaryDirectory()
            temp_path = Path(temp_dir.name)

            logger.info(f"Converting PDF pages to images: {pdf_path.name}")

            # Convert PDF pages to images
            loop = asyncio.get_event_loop()
            images = await loop.run_in_executor(
                self.executor,
                convert_from_path,
                str(pdf_path),
                300  # DPI
            )

            logger.info(f"Processing {len(images)} pages with OCR")

            # Process each page
            all_text = []
            all_confidences = []

            for i, image in enumerate(images, 1):
                # Save image temporarily
                image_path = temp_path / f"page_{i}.png"
                image.save(image_path, "PNG")

                # Extract text from page
                text, confidence = await self.extract_text_from_image(image_path, lang)
                all_text.append(text)
                all_confidences.append(confidence)

                logger.debug(f"Page {i}/{len(images)}: {len(text)} chars, confidence {confidence:.2f}")

            # Combine results
            combined_text = "\n\n".join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

            logger.info(
                f"OCR completed: {len(combined_text)} total characters, "
                f"average confidence: {avg_confidence:.2f}"
            )

            return combined_text, avg_confidence

        except Exception as e:
            logger.error(f"PDF OCR failed for {pdf_path}: {e}")
            raise
        finally:
            # Clean up temporary files
            if temp_dir:
                try:
                    temp_dir.cleanup()
                    logger.debug("Temporary files cleaned up")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp files: {e}")

    def __del__(self):
        """Clean up executor on deletion."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
