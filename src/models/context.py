"""
Context model for organizing documents into separate collections.
"""
import re
from datetime import datetime
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field, field_validator


class Context(BaseModel):
    """
    Context entity for organizing documents into logical groups.

    Each context maps to a separate ChromaDB collection for isolation.
    Documents can belong to multiple contexts simultaneously.
    """

    name: str = Field(..., description="Unique context name (alphanumeric, dash, underscore, 1-64 chars)")
    description: Optional[str] = Field(None, description="Optional human-readable description")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    document_count: int = Field(default=0, description="Number of documents in this context")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")
    
    # Validation pattern: alphanumeric + dash + underscore, 1-64 chars
    NAME_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
    RESERVED_NAMES: ClassVar[set] = {"default"}

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate context name follows naming rules.

        Rules:
        - Only alphanumeric characters, dashes, and underscores
        - Length: 1-64 characters
        - "default" is reserved (can exist but cannot be created/deleted by user)

        Args:
            v: Context name to validate

        Returns:
            Validated context name

        Raises:
            ValueError: If name is invalid
        """
        if not v or not v.strip():
            raise ValueError("Context name cannot be empty")

        v = v.strip()

        if not cls.NAME_PATTERN.match(v):
            raise ValueError(
                "Context name must be alphanumeric with dashes/underscores only, "
                "and between 1-64 characters"
            )

        return v

    @field_validator("document_count")
    @classmethod
    def validate_document_count(cls, v: int) -> int:
        """Ensure document count is non-negative."""
        if v < 0:
            raise ValueError("Document count cannot be negative")
        return v

    def is_reserved(self) -> bool:
        """Check if this context name is reserved."""
        return self.name in self.RESERVED_NAMES
