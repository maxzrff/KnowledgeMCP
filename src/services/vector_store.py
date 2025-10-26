"""
ChromaDB client wrapper for vector storage.
"""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class VectorStore:
    """ChromaDB wrapper for vector storage operations."""

    def __init__(self, persist_directory: Path):
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Directory for persistent storage
        """
        self.persist_directory = persist_directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        logger.info(f"ChromaDB initialized at {persist_directory}")

    def get_or_create_collection(self, name: str = "knowledge_base_documents") -> Collection:
        """
        Get or create a collection for storing embeddings.

        Args:
            name: Collection name

        Returns:
            ChromaDB collection instance
        """
        return self._client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})

    async def add_embeddings(
        self,
        collection_name: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """
        Add embeddings to the vector store.

        Args:
            collection_name: Name of the collection
            ids: List of unique IDs for each embedding
            embeddings: List of embedding vectors
            documents: List of text documents
            metadatas: List of metadata dictionaries
        """
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(ids)} embeddings to collection '{collection_name}'")

    async def search(
        self,
        collection_name: str,
        query_embedding: list[float],
        top_k: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Search for similar embeddings in the vector store.

        Args:
            collection_name: Name of the collection
            query_embedding: Query embedding vector
            top_k: Number of results to return
            where: Optional metadata filters

        Returns:
            Dictionary with search results
        """
        collection = self.get_or_create_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )

        logger.info(f"Search in '{collection_name}': found {len(results['ids'][0])} results")

        return results

    def get_all_documents(self, collection_name: str = "knowledge_base_documents") -> dict[str, Any]:
        """
        Get all documents from the vector store.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with ids, documents, metadatas, embeddings
        """
        collection = self.get_or_create_collection(collection_name)
        count = collection.count()
        
        if count == 0:
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
        
        # Get all items (ChromaDB default limit is 10, so we need to specify)
        results = collection.get(
            limit=count,
            include=["metadatas", "documents"]
        )
        
        logger.info(f"Retrieved {count} documents from collection '{collection_name}'")
        return results

    def reset(self) -> None:
        """Reset the entire database (for testing)."""
        self._client.reset()
        logger.warning("ChromaDB reset - all data deleted")
