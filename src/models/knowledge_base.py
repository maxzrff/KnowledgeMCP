"""
Knowledge base aggregate model.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field


class KnowledgeBase(BaseModel):
    """Knowledge base aggregate."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "default"
    document_count: int = 0
    embedding_count: int = 0
    total_size_bytes: int = 0
    storage_path: Path
    vector_db_path: Path
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def average_chunks_per_document(self) -> float:
        """Calculate average chunks per document."""
        if self.document_count == 0:
            return 0.0
        return self.embedding_count / self.document_count
    
    @property
    def storage_size_mb(self) -> float:
        """Calculate storage size in MB."""
        return self.total_size_bytes / (1024 * 1024)
