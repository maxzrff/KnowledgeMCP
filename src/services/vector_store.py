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
    """ChromaDB wrapper for vector storage operations with multi-context support."""

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
    
    @staticmethod
    def _collection_name(context: str) -> str:
        """
        Get collection name for a context.
        
        Args:
            context: Context name
            
        Returns:
            ChromaDB collection name
        """
        return f"context_{context}"
    
    @staticmethod
    def _context_from_collection(collection_name: str) -> str | None:
        """
        Extract context name from collection name.
        
        Args:
            collection_name: ChromaDB collection name
            
        Returns:
            Context name or None if not a context collection
        """
        if collection_name.startswith("context_"):
            return collection_name[8:]  # Remove "context_" prefix
        return None

    def get_collection(self, context: str = "default") -> Collection:
        """
        Get or create a collection for a specific context.

        Args:
            context: Context name (default: "default")

        Returns:
            ChromaDB collection instance
        """
        collection_name = self._collection_name(context)
        return self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine", "context": context}
        )
    
    def create_collection(self, context: str) -> Collection:
        """
        Create a new collection for a context.
        
        Args:
            context: Context name
            
        Returns:
            ChromaDB collection instance
        """
        collection_name = self._collection_name(context)
        collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine", "context": context}
        )
        logger.info(f"Created collection for context: {context}")
        return collection
    
    def delete_collection(self, context: str) -> None:
        """
        Delete a collection and all its vectors.
        
        Args:
            context: Context name
        """
        collection_name = self._collection_name(context)
        try:
            self._client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection for context: {context}")
        except Exception as e:
            logger.warning(f"Could not delete collection {collection_name}: {e}")
    
    def list_collections(self) -> list[str]:
        """
        List all context names from collections.
        
        Returns:
            List of context names
        """
        collections = self._client.list_collections()
        contexts = []
        for collection in collections:
            context = self._context_from_collection(collection.name)
            if context:
                contexts.append(context)
        return contexts

    def get_or_create_collection(self, name: str = "knowledge_base_documents") -> Collection:
        """
        Get or create a collection for storing embeddings (legacy method).

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
        context: str = "default",
    ) -> None:
        """
        Add embeddings to the vector store.

        Args:
            collection_name: Name of the collection (legacy parameter, will be replaced by context)
            ids: List of unique IDs for each embedding
            embeddings: List of embedding vectors
            documents: List of text documents
            metadatas: List of metadata dictionaries
            context: Context name for multi-context support
        """
        collection = self.get_collection(context)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(ids)} embeddings to context '{context}'")

    async def search(
        self,
        collection_name: str,
        query_embedding: list[float],
        top_k: int = 10,
        where: dict[str, Any] | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        """
        Search for similar embeddings in the vector store.

        Args:
            collection_name: Name of the collection (legacy parameter)
            query_embedding: Query embedding vector
            top_k: Number of results to return
            where: Optional metadata filters
            context: Optional context name (None = search all contexts)

        Returns:
            Dictionary with search results
        """
        if context:
            # Search specific context
            collection = self.get_collection(context)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
            )
            logger.info(f"Search in context '{context}': found {len(results['ids'][0])} results")
            return results
        else:
            # Search across all contexts
            all_contexts = self.list_collections()
            if not all_contexts:
                # No contexts, return empty results
                return {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}
            
            # Collect results from all contexts
            all_results = {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}
            for ctx in all_contexts:
                collection = self.get_collection(ctx)
                try:
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k,
                        where=where,
                    )
                    # Merge results
                    all_results["ids"][0].extend(results["ids"][0])
                    all_results["distances"][0].extend(results["distances"][0])
                    all_results["metadatas"][0].extend(results["metadatas"][0])
                    all_results["documents"][0].extend(results["documents"][0])
                except Exception as e:
                    logger.warning(f"Error searching context '{ctx}': {e}")
            
            # Sort by distance and take top_k
            if all_results["ids"][0]:
                combined = list(zip(
                    all_results["ids"][0],
                    all_results["distances"][0],
                    all_results["metadatas"][0],
                    all_results["documents"][0]
                ))
                combined.sort(key=lambda x: x[1])  # Sort by distance
                combined = combined[:top_k]
                
                all_results = {
                    "ids": [[x[0] for x in combined]],
                    "distances": [[x[1] for x in combined]],
                    "metadatas": [[x[2] for x in combined]],
                    "documents": [[x[3] for x in combined]],
                }
            
            logger.info(f"Cross-context search: found {len(all_results['ids'][0])} results")
            return all_results

    def get_all_documents(self, collection_name: str = "knowledge_base_documents", context: str | None = None) -> dict[str, Any]:
        """
        Get all documents from the vector store.

        Args:
            collection_name: Name of the collection (legacy parameter)
            context: Optional context name (None = all contexts)

        Returns:
            Dictionary with ids, documents, metadatas, embeddings
        """
        if context:
            # Get from specific context
            collection = self.get_collection(context)
            count = collection.count()
            
            if count == 0:
                return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
            
            results = collection.get(
                limit=count,
                include=["metadatas", "documents"]
            )
            
            logger.info(f"Retrieved {count} documents from context '{context}'")
            return results
        else:
            # Get from all contexts
            all_contexts = self.list_collections()
            if not all_contexts:
                return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
            
            all_results = {"ids": [], "documents": [], "metadatas": []}
            for ctx in all_contexts:
                collection = self.get_collection(ctx)
                count = collection.count()
                if count > 0:
                    results = collection.get(
                        limit=count,
                        include=["metadatas", "documents"]
                    )
                    all_results["ids"].extend(results.get("ids", []))
                    all_results["documents"].extend(results.get("documents", []))
                    all_results["metadatas"].extend(results.get("metadatas", []))
            
            logger.info(f"Retrieved {len(all_results['ids'])} documents from all contexts")
            return all_results

    def reset(self) -> None:
        """Reset the entire database (for testing)."""
        self._client.reset()
        logger.warning("ChromaDB reset - all data deleted")
