"""
Text chunking strategies for document processing.
"""

import re
from typing import Literal

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def chunk_by_sentences(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Chunk text by sentences with overlap.

    Args:
        text: Input text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap size in characters

    Returns:
        List of text chunks
    """
    # Split into sentences using simple regex
    sentence_pattern = r"(?<=[.!?])\s+(?=[A-Z])"
    sentences = re.split(sentence_pattern, text)

    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_size = len(sentence)

        if current_size + sentence_size > chunk_size and current_chunk:
            # Save current chunk
            chunks.append(" ".join(current_chunk))

            # Start new chunk with overlap
            overlap_sentences = []
            overlap_size = 0
            for s in reversed(current_chunk):
                if overlap_size + len(s) <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_size += len(s)
                else:
                    break

            current_chunk = overlap_sentences
            current_size = overlap_size

        current_chunk.append(sentence)
        current_size += sentence_size

    # Add remaining chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def chunk_by_paragraphs(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Chunk text by paragraphs with overlap.

    Args:
        text: Input text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap size in characters

    Returns:
        List of text chunks
    """
    paragraphs = text.split("\n\n")

    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_size = len(para)

        if current_size + para_size > chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))

            # Overlap handling
            if current_chunk and len(current_chunk[-1]) <= overlap:
                current_chunk = [current_chunk[-1]]
                current_size = len(current_chunk[-1])
            else:
                current_chunk = []
                current_size = 0

        current_chunk.append(para)
        current_size += para_size

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def chunk_by_fixed_size(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Chunk text by fixed character size with overlap.

    Args:
        text: Input text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap size in characters

    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def chunk_text(
    text: str,
    strategy: Literal["sentence", "paragraph", "fixed"] = "sentence",
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Chunk text using specified strategy.

    Args:
        text: Input text to chunk
        strategy: Chunking strategy to use
        chunk_size: Target chunk size in characters
        overlap: Overlap size in characters

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    if strategy == "sentence":
        chunks = chunk_by_sentences(text, chunk_size, overlap)
    elif strategy == "paragraph":
        chunks = chunk_by_paragraphs(text, chunk_size, overlap)
    elif strategy == "fixed":
        chunks = chunk_by_fixed_size(text, chunk_size, overlap)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")

    logger.debug(f"Created {len(chunks)} chunks using {strategy} strategy")
    return chunks
