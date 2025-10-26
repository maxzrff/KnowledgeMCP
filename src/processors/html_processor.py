"""
HTML document processor.
"""

from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from src.models.document import DocumentFormat
from src.processors.base import BaseProcessor
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class HTMLProcessor(BaseProcessor):
    """HTML document processor."""

    @property
    def supported_format(self) -> DocumentFormat:
        return DocumentFormat.HTML

    async def extract_text(self, file_path: Path) -> str:
        """Extract text from HTML."""
        try:
            with open(file_path, encoding="utf-8") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "lxml")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text(separator="\n", strip=True)
            logger.info(f"Extracted {len(text)} characters from HTML: {file_path.name}")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from HTML {file_path}: {e}")
            raise

    async def extract_metadata(self, file_path: Path) -> dict[str, Any]:
        """Extract metadata from HTML."""
        try:
            with open(file_path, encoding="utf-8") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "lxml")
            metadata = {"format": "html"}

            # Extract title
            if soup.title:
                metadata["title"] = soup.title.string

            # Extract meta tags
            for meta in soup.find_all("meta"):
                if meta.get("name") == "author":
                    metadata["author"] = meta.get("content")
                elif meta.get("name") == "description":
                    metadata["description"] = meta.get("content")

            return metadata
        except Exception as e:
            logger.warning(f"Failed to extract HTML metadata: {e}")
            return {"format": "html"}
