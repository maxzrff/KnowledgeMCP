"""
PDF document processor.
"""

from pathlib import Path
from typing import Any

import pdfplumber
import PyPDF2

from src.models.document import DocumentFormat
from src.processors.base import BaseProcessor
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class PDFProcessor(BaseProcessor):
    """PDF document processor."""

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
