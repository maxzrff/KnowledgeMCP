"""
PDF document processor with smart OCR fallback.
"""

from pathlib import Path
from typing import Any, Optional

import pdfplumber
import PyPDF2

from src.models.document import DocumentFormat, ProcessingMethod
from src.processors.base import BaseProcessor
from src.services.ocr_service import OCRService
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class PDFProcessor(BaseProcessor):
    """PDF document processor with automatic OCR fallback."""

    def __init__(self, ocr_service: Optional[OCRService] = None):
        """
        Initialize PDF processor.

        Args:
            ocr_service: Optional OCR service for fallback processing
        """
        self.ocr_service = ocr_service

    @property
    def supported_format(self) -> DocumentFormat:
        return DocumentFormat.PDF

    async def extract_text(self, file_path: Path) -> str:
        """Extract text from PDF using pdfplumber."""
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(text)} characters from PDF: {file_path.name}")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            raise

    async def extract_metadata(self, file_path: Path) -> dict[str, Any]:
        """Extract metadata from PDF."""
        try:
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                metadata = {
                    "page_count": len(pdf_reader.pages),
                    "format": "pdf",
                }

                # Add document info if available
                if pdf_reader.metadata:
                    info = pdf_reader.metadata
                    if info.get("/Title"):
                        metadata["title"] = str(info["/Title"])
                    if info.get("/Author"):
                        metadata["author"] = str(info["/Author"])
                    if info.get("/Subject"):
                        metadata["subject"] = str(info["/Subject"])

                return metadata
        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {e}")
            return {"format": "pdf"}

    async def process(self, file_path: Path) -> tuple[str, dict[str, Any], ProcessingMethod]:
        """
        Process PDF with automatic OCR fallback for scan-only documents.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (text_content, metadata, processing_method)
        """
        # Extract text using standard method
        extracted_text = await self.extract_text(file_path)
        metadata = await self.extract_metadata(file_path)

        # Check if OCR is needed and available
        if self.ocr_service:
            needs_ocr = await self.ocr_service.is_ocr_needed(extracted_text)
            
            if needs_ocr:
                logger.info(f"Text quality insufficient - using OCR for {file_path.name}")
                try:
                    ocr_text, confidence = await self.ocr_service.process_pdf_with_ocr(file_path)
                    
                    # Add OCR metadata
                    metadata["ocr_confidence"] = confidence
                    metadata["ocr_used"] = True
                    
                    logger.info(
                        f"OCR completed for {file_path.name}: "
                        f"{len(ocr_text)} characters (confidence: {confidence:.2f})"
                    )
                    
                    return ocr_text, metadata, ProcessingMethod.OCR
                    
                except Exception as e:
                    logger.error(f"OCR processing failed: {e}")
                    logger.info("Falling back to extracted text despite poor quality")
                    metadata["ocr_failed"] = True
                    metadata["ocr_error"] = str(e)
                    # Fall through to return extracted text

        # Return extracted text (good quality or OCR not available/failed)
        metadata["ocr_used"] = False
        return extracted_text, metadata, ProcessingMethod.TEXT_EXTRACTION
