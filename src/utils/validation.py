"""
File format validation utilities.
"""

from pathlib import Path

from src.models.document import DocumentFormat

SUPPORTED_FORMATS = {
    ".pdf": DocumentFormat.PDF,
    ".docx": DocumentFormat.DOCX,
    ".pptx": DocumentFormat.PPTX,
    ".xlsx": DocumentFormat.XLSX,
    ".html": DocumentFormat.HTML,
    ".htm": DocumentFormat.HTML,
    ".jpg": DocumentFormat.JPG,
    ".jpeg": DocumentFormat.JPG,
    ".png": DocumentFormat.PNG,
    ".svg": DocumentFormat.SVG,
}


def validate_file_format(file_path: Path) -> DocumentFormat:
    """
    Validate file format and return DocumentFormat enum.

    Args:
        file_path: Path to the file

    Returns:
        DocumentFormat enum value

    Raises:
        ValueError: If format is not supported
    """
    suffix = file_path.suffix.lower()

    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS.keys())}"
        )

    return SUPPORTED_FORMATS[suffix]


def validate_file_exists(file_path: Path) -> None:
    """
    Validate that file exists and is readable.

    Args:
        file_path: Path to the file

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file is not readable
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    if not file_path.stat().st_size > 0:
        raise ValueError(f"File is empty: {file_path}")


def validate_file_size(file_path: Path, max_size_mb: int) -> None:
    """
    Validate file size is within limits.

    Args:
        file_path: Path to the file
        max_size_mb: Maximum allowed size in MB

    Raises:
        ValueError: If file is too large
    """
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > max_size_mb:
        raise ValueError(
            f"File size ({size_mb:.1f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
        )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove potentially dangerous characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path traversal attempts
    filename = Path(filename).name

    # Replace potentially dangerous characters
    unsafe_chars = ["/", "\\", "\x00", ".."]
    for char in unsafe_chars:
        filename = filename.replace(char, "_")

    return filename
