"""
OCR service using Tesseract.
"""

from pathlib import Path

try:
    import pytesseract
    from PIL import Image

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class OCRService:
    """Service for OCR processing using Tesseract."""

    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize OCR service.

        Args:
            confidence_threshold: Minimum confidence score for OCR results
        """
        self.confidence_threshold = confidence_threshold

        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract OCR not available - install pytesseract and tesseract-ocr")

    async def extract_text_from_image(
        self,
        image_path: Path,
        language: str = "eng",
    ) -> tuple[str, float]:
        """
        Extract text from image using OCR.

        Args:
            image_path: Path to image file
            language: OCR language code

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract OCR not available")

        try:
            # Load and preprocess image
            image = Image.open(image_path)

            # Convert to grayscale
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

            logger.info(
                f"OCR extracted {len(text)} characters from {image_path.name} "
                f"(confidence: {confidence_score:.2f})"
            )

            return text, confidence_score
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            raise

    async def is_ocr_needed(self, extracted_text: str) -> bool:
        """
        Determine if OCR is needed based on extracted text quality.

        Args:
            extracted_text: Text extracted from document

        Returns:
            True if OCR is recommended
        """
        # Heuristics for OCR decision
        text_length = len(extracted_text.strip())

        # Too little text suggests scanned document
        if text_length < 100:
            return True

        # Check for gibberish (high ratio of non-alphanumeric characters)
        alphanumeric = sum(c.isalnum() or c.isspace() for c in extracted_text)
        ratio = alphanumeric / len(extracted_text) if extracted_text else 0

        if ratio < 0.7:  # Less than 70% readable characters
            return True

        return False
