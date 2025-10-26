"""
Base processor interface for document processing.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.models.document import DocumentFormat, ProcessingMethod


class BaseProcessor(ABC):
    """Base interface for document processors."""

    @property
    @abstractmethod
    def supported_format(self) -> DocumentFormat:
        """Return the document format this processor supports."""
        pass

    @abstractmethod
    async def extract_text(self, file_path: Path) -> str:
        """
        Extract text content from the document.

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text content

        Raises:
            Exception: If extraction fails
        """
        pass

    @abstractmethod
    async def extract_metadata(self, file_path: Path) -> dict[str, Any]:
        """
        Extract metadata from the document.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary of metadata (author, title, page count, etc.)
        """
        pass

    async def process(self, file_path: Path) -> tuple[str, dict[str, Any], ProcessingMethod]:
        """
        Process the document and extract text and metadata.

        Args:
            file_path: Path to the document file

        Returns:
            Tuple of (text_content, metadata, processing_method)
        """
        text = await self.extract_text(file_path)
        metadata = await self.extract_metadata(file_path)
        return text, metadata, ProcessingMethod.TEXT_EXTRACTION
