"""
Search result entity model.
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class SearchResult(BaseModel):
    """Search result entity."""
    
    document_id: str
    chunk_id: str
    chunk_text: str
    relevance_score: float
    document_metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    highlight: Optional[str] = None
    
    @field_validator("relevance_score")
    @classmethod
    def validate_relevance_score(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Relevance score must be between 0.0 and 1.0")
        return v
    
    @field_validator("chunk_text")
    @classmethod
    def validate_chunk_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Chunk text cannot be empty")
        return v
