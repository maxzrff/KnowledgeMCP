"""
Text extraction service coordinating document processors.
"""

from pathlib import Path
from typing import Any

from src.models.document import DocumentFormat, ProcessingMethod
from src.processors.docx_processor import DOCXProcessor
from src.processors.html_processor import HTMLProcessor
from src.processors.image_processor import ImageProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.pptx_processor import PPTXProcessor
from src.processors.xlsx_processor import XLSXProcessor
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TextExtractor:
    """Service for extracting text from various document formats."""

    def __init__(self):
        self._processors = {
            DocumentFormat.PDF: PDFProcessor(),
            DocumentFormat.DOCX: DOCXProcessor(),
            DocumentFormat.PPTX: PPTXProcessor(),
            DocumentFormat.XLSX: XLSXProcessor(),
            DocumentFormat.HTML: HTMLProcessor(),
            DocumentFormat.JPG: ImageProcessor(DocumentFormat.JPG),
            DocumentFormat.PNG: ImageProcessor(DocumentFormat.PNG),
            DocumentFormat.SVG: ImageProcessor(DocumentFormat.SVG),
        }

    async def extract(
        self,
        file_path: Path,
        document_format: DocumentFormat,
    ) -> tuple[str, dict[str, Any], ProcessingMethod]:
        """
        Extract text and metadata from document.

        Args:
            file_path: Path to document file
            document_format: Document format

        Returns:
            Tuple of (text, metadata, processing_method)
        """
        processor = self._processors.get(document_format)
        if not processor:
            raise ValueError(f"No processor available for format: {document_format}")

        logger.info(f"Extracting text from {file_path.name} ({document_format.value})")
        return await processor.process(file_path)
