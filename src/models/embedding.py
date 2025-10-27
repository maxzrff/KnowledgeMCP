"""
Embedding entity model.
"""
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class Embedding(BaseModel):
    """Embedding entity for document chunks."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    chunk_index: int
    chunk_text: str
    vector: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("chunk_index")
    @classmethod
    def validate_chunk_index(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Chunk index cannot be negative")
        return v
    
    @field_validator("chunk_text")
    @classmethod
    def validate_chunk_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Chunk text cannot be empty")
        return v
    
    @field_validator("vector")
    @classmethod
    def validate_vector(cls, v: List[float]) -> List[float]:
        if len(v) != 384:  # all-MiniLM-L6-v2 dimensionality
            raise ValueError(f"Vector must have 384 dimensions, got {len(v)}")
        return v
