"""
Document models and enums for the knowledge server.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class DocumentFormat(str, Enum):
    """Supported document formats."""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    HTML = "html"
    JPG = "jpg"
    PNG = "png"
    SVG = "svg"


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ProcessingMethod(str, Enum):
    """Method used to extract content from document."""
    TEXT_EXTRACTION = "text_extraction"
    OCR = "ocr"
    HYBRID = "hybrid"
    IMAGE_ANALYSIS = "image_analysis"


class TaskStatus(str, Enum):
    """Status of async processing task."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Document(BaseModel):
    """Document entity with metadata and multi-context support."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    file_path: str
    content_hash: str
    format: DocumentFormat
    size_bytes: int
    date_added: datetime = Field(default_factory=datetime.utcnow)
    date_modified: datetime = Field(default_factory=datetime.utcnow)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_method: Optional[ProcessingMethod] = None
    chunk_count: int = 0
    embedding_ids: List[str] = Field(default_factory=list)
    contexts: List[str] = Field(
        default_factory=lambda: ["default"],
        description="List of context names this document belongs to"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        invalid_chars = ['/', '\\', '\x00']
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Filename contains invalid characters: {invalid_chars}")
        return v
    
    @field_validator("size_bytes")
    @classmethod
    def validate_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("File size must be greater than 0")
        return v
    
    @field_validator("chunk_count")
    @classmethod
    def validate_chunk_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Chunk count cannot be negative")
        return v
    
    @field_validator("contexts")
    @classmethod
    def validate_contexts(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("Document must belong to at least one context")
        return v


class ProcessingTask(BaseModel):
    """Async document processing task with progress tracking."""
    
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    status: TaskStatus = TaskStatus.QUEUED
    progress: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Progress must be between 0.0 and 1.0")
        return v
    
    @field_validator("completed_steps")
    @classmethod
    def validate_completed_steps(cls, v: int, info: Any) -> int:
        total_steps = info.data.get("total_steps", 0)
        if v > total_steps:
            raise ValueError("Completed steps cannot exceed total steps")
        return v
