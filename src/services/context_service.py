"""
Service for managing contexts (document collections).
"""
from datetime import datetime
from typing import Any, Optional

from src.models.context import Context
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ContextNotFoundError(Exception):
    """Raised when a context is not found."""


class ContextAlreadyExistsError(Exception):
    """Raised when attempting to create a duplicate context."""


class ReservedContextError(Exception):
    """Raised when attempting to delete a reserved context."""


class ContextService:
    """Service for context CRUD operations."""

    def __init__(self):
        """Initialize context service with default context."""
        self._contexts: dict[str, Context] = {}
        # Always create default context
        self._contexts["default"] = Context(
            name="default",
            description="Default context for all documents",
            created_at=datetime.utcnow(),
        )
        logger.info("ContextService initialized with default context")

    def create_context(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> Context:
        """
        Create a new context.

        Args:
            name: Unique context name
            description: Optional description
            metadata: Optional metadata dictionary

        Returns:
            Created Context object

        Raises:
            ContextAlreadyExistsError: If context already exists
            ValueError: If name is invalid or reserved
        """
        # Validate name (will raise ValueError if invalid)
        context = Context(
            name=name,
            description=description,
            metadata=metadata or {}
        )

        # Check for reserved names
        if context.is_reserved():
            raise ValueError(f"Context name '{name}' is reserved and cannot be created")

        # Check for duplicates
        if name in self._contexts:
            raise ContextAlreadyExistsError(f"Context '{name}' already exists")

        self._contexts[name] = context
        logger.info(f"Created context: {name}")

        return context

    def list_contexts(self) -> list[Context]:
        """
        List all contexts with document counts.

        Returns:
            List of Context objects sorted by name (default first)
        """
        contexts = list(self._contexts.values())
        # Sort: default first, then alphabetically
        contexts.sort(key=lambda c: ("" if c.name == "default" else c.name))
        return contexts

    def get_context(self, name: str) -> Context:
        """
        Get a specific context by name.

        Args:
            name: Context name

        Returns:
            Context object

        Raises:
            ContextNotFoundError: If context doesn't exist
        """
        context = self._contexts.get(name)
        if not context:
            raise ContextNotFoundError(f"Context '{name}' not found")
        return context

    def context_exists(self, name: str) -> bool:
        """
        Check if a context exists.

        Args:
            name: Context name

        Returns:
            True if context exists, False otherwise
        """
        return name in self._contexts

    def delete_context(self, name: str) -> str:
        """
        Delete a context.

        Args:
            name: Context name to delete

        Returns:
            Success confirmation message

        Raises:
            ContextNotFoundError: If context doesn't exist
            ReservedContextError: If attempting to delete reserved context
        """
        context = self.get_context(name)

        if context.is_reserved():
            raise ReservedContextError(f"Context '{name}' is reserved and cannot be deleted")

        del self._contexts[name]
        logger.info(f"Deleted context: {name}")

        return f"Context '{name}' deleted successfully"

    def update_document_count(self, name: str, count: int) -> None:
        """
        Update document count for a context.

        Args:
            name: Context name
            count: New document count

        Raises:
            ContextNotFoundError: If context doesn't exist
        """
        context = self.get_context(name)
        context.document_count = count
        context.updated_at = datetime.utcnow()

    def increment_document_count(self, name: str) -> None:
        """
        Increment document count for a context.

        Args:
            name: Context name

        Raises:
            ContextNotFoundError: If context doesn't exist
        """
        context = self.get_context(name)
        context.document_count += 1
        context.updated_at = datetime.utcnow()

    def decrement_document_count(self, name: str) -> None:
        """
        Decrement document count for a context.

        Args:
            name: Context name

        Raises:
            ContextNotFoundError: If context doesn't exist
        """
        context = self.get_context(name)
        if context.document_count > 0:
            context.document_count -= 1
        context.updated_at = datetime.utcnow()
