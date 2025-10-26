"""
Unit tests for Document model validation.
"""

import pytest

from src.models.document import (
    Document,
    DocumentFormat,
    ProcessingStatus,
    ProcessingTask,
    TaskStatus,
)


class TestDocumentModel:
    """Test Document model validation."""

    def test_document_creation_with_defaults(self):
        """Test creating a document with default values."""
        doc = Document(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            content_hash="abc123",
            format=DocumentFormat.PDF,
            size_bytes=1024,
        )

        assert doc.id is not None
        assert doc.filename == "test.pdf"
        assert doc.processing_status == ProcessingStatus.PENDING
        assert doc.chunk_count == 0
        assert doc.embedding_ids == []
        assert doc.metadata == {}

    def test_document_invalid_filename(self):
        """Test document creation with invalid filename."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            Document(
                filename="",
                file_path="/path/to/test.pdf",
                content_hash="abc123",
                format=DocumentFormat.PDF,
                size_bytes=1024,
            )

    def test_document_invalid_filename_with_slash(self):
        """Test document creation with invalid filename characters."""
        with pytest.raises(ValueError, match="invalid characters"):
            Document(
                filename="test/file.pdf",
                file_path="/path/to/test.pdf",
                content_hash="abc123",
                format=DocumentFormat.PDF,
                size_bytes=1024,
            )

    def test_document_invalid_size(self):
        """Test document creation with invalid size."""
        with pytest.raises(ValueError, match="File size must be greater than 0"):
            Document(
                filename="test.pdf",
                file_path="/path/to/test.pdf",
                content_hash="abc123",
                format=DocumentFormat.PDF,
                size_bytes=0,
            )

    def test_document_invalid_chunk_count(self):
        """Test document creation with negative chunk count."""
        with pytest.raises(ValueError, match="Chunk count cannot be negative"):
            Document(
                filename="test.pdf",
                file_path="/path/to/test.pdf",
                content_hash="abc123",
                format=DocumentFormat.PDF,
                size_bytes=1024,
                chunk_count=-1,
            )


class TestProcessingTask:
    """Test ProcessingTask model validation."""

    def test_task_creation_with_defaults(self):
        """Test creating a task with default values."""
        task = ProcessingTask(
            document_id="doc123",
        )

        assert task.task_id is not None
        assert task.document_id == "doc123"
        assert task.status == TaskStatus.QUEUED
        assert task.progress == 0.0
        assert task.completed_steps == 0

    def test_task_invalid_progress(self):
        """Test task creation with invalid progress."""
        with pytest.raises(ValueError, match="Progress must be between 0.0 and 1.0"):
            ProcessingTask(
                document_id="doc123",
                progress=1.5,
            )

    def test_task_invalid_completed_steps(self):
        """Test task creation with invalid completed steps."""
        with pytest.raises(ValueError, match="Completed steps cannot exceed total steps"):
            ProcessingTask(
                document_id="doc123",
                total_steps=5,
                completed_steps=10,
            )
