"""
Core knowledge service for document management.
"""

import asyncio
import hashlib
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.config.settings import get_settings
from src.models.document import (
    Document,
    DocumentFormat,
    ProcessingStatus,
    ProcessingTask,
    TaskStatus,
)
from src.services.embedding_service import EmbeddingService
from src.services.text_extractor import TextExtractor
from src.services.vector_store import VectorStore
from src.utils.chunking import chunk_text
from src.utils.logging_config import get_logger
from src.utils.validation import validate_file_exists, validate_file_format, validate_file_size

logger = get_logger(__name__)


class KnowledgeService:
    """Core service for knowledge base operations."""

    def __init__(self):
        self.settings = get_settings()
        self.text_extractor = TextExtractor()
        self.embedding_service = EmbeddingService(
            model_name=self.settings.embedding.model_name,
            device=self.settings.embedding.device,
            cache_folder=self.settings.storage.model_cache_path,
        )
        self.vector_store = VectorStore(self.settings.storage.vector_db_path)
        self._tasks: dict[str, ProcessingTask] = {}
        self._documents: dict[str, Document] = {}

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def add_document(
        self,
        file_path: Path,
        metadata: dict[str, Any] | None = None,
        async_processing: bool = True,
    ) -> str:
        """
        Add a document to the knowledge base.

        Args:
            file_path: Path to the document file
            metadata: Optional metadata dictionary
            async_processing: If True, process asynchronously and return task ID

        Returns:
            Task ID if async, document ID if sync
        """
        # Validation
        validate_file_exists(file_path)
        document_format = validate_file_format(file_path)
        validate_file_size(file_path, self.settings.processing.max_file_size_mb)

        # Calculate hash for deduplication
        content_hash = self._calculate_file_hash(file_path)

        # Check for duplicates
        for doc in self._documents.values():
            if doc.content_hash == content_hash:
                logger.info(f"Duplicate document detected: {file_path.name}")
                return doc.id

        # Create document
        document = Document(
            filename=file_path.name,
            file_path=str(file_path),
            content_hash=content_hash,
            format=document_format,
            size_bytes=file_path.stat().st_size,
            metadata=metadata or {},
        )

        self._documents[document.id] = document

        if async_processing:
            # Create async task
            task = ProcessingTask(document_id=document.id, total_steps=4)
            self._tasks[task.task_id] = task

            # Start processing in background
            asyncio.create_task(self._process_document_async(task.task_id, document))

            logger.info(f"Document queued for async processing: {file_path.name}")
            return task.task_id
        # Process synchronously
        await self._process_document(document)
        return document.id

    async def _process_document_async(self, task_id: str, document: Document) -> None:
        """Process document asynchronously with progress tracking."""
        task = self._tasks[task_id]
        task.status = TaskStatus.RUNNING

        try:
            task.current_step = "Extracting text"
            task.completed_steps = 1
            task.progress = 0.25

            await self._process_document(document)

            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            task.completed_steps = task.total_steps
            logger.info(f"Document processing completed: {document.filename}")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            document.processing_status = ProcessingStatus.FAILED
            document.error_message = str(e)
            logger.error(f"Document processing failed: {e}")

    async def _process_document(self, document: Document) -> None:
        """Process a single document."""
        document.processing_status = ProcessingStatus.PROCESSING

        # Extract text
        text, metadata, processing_method = await self.text_extractor.extract(
            Path(document.file_path),
            document.format,
        )

        document.processing_method = processing_method
        document.metadata.update(metadata)

        if not text or len(text.strip()) < 10:
            logger.warning(f"No text extracted from {document.filename}")
            document.processing_status = ProcessingStatus.COMPLETED
            return

        # Chunk text
        chunks = chunk_text(
            text,
            strategy=self.settings.chunking.strategy,
            chunk_size=self.settings.chunking.chunk_size,
            overlap=self.settings.chunking.chunk_overlap,
        )

        if not chunks:
            logger.warning(f"No chunks created from {document.filename}")
            document.processing_status = ProcessingStatus.COMPLETED
            return

        # Generate embeddings
        embeddings = await self.embedding_service.encode(
            chunks,
            batch_size=self.settings.embedding.batch_size,
        )

        # Store in vector database
        embedding_ids = []
        embedding_metadatas = []

        for i, (_chunk, _embedding_vector) in enumerate(zip(chunks, embeddings, strict=True)):
            embedding_id = str(uuid4())
            embedding_ids.append(embedding_id)

            embedding_metadatas.append(
                {
                    "document_id": document.id,
                    "filename": document.filename,
                    "chunk_index": i,
                    "format": document.format.value,
                    "processing_method": (
                        document.processing_method.value
                        if document.processing_method
                        else "unknown"
                    ),
                }
            )

        # Add to vector store
        await self.vector_store.add_embeddings(
            collection_name="knowledge_base_documents",
            ids=embedding_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=embedding_metadatas,
        )

        # Update document
        document.chunk_count = len(chunks)
        document.embedding_ids = embedding_ids
        document.processing_status = ProcessingStatus.COMPLETED

        logger.info(
            f"Document processed: {document.filename} - "
            f"{len(chunks)} chunks, {len(embeddings)} embeddings"
        )

    def get_task_status(self, task_id: str) -> ProcessingTask | None:
        """Get status of processing task."""
        return self._tasks.get(task_id)

    def list_documents(self) -> list[Document]:
        """List all documents in knowledge base."""
        return list(self._documents.values())

    def get_document(self, document_id: str) -> Document | None:
        """Get a specific document by ID."""
        return self._documents.get(document_id)

    async def search(
        self,
        query: str,
        top_k: int = 10,
        min_relevance: float = 0.0,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search the knowledge base using natural language query.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            min_relevance: Minimum relevance score threshold
            filters: Optional metadata filters

        Returns:
            List of search results with relevance scores
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Generate query embedding
        query_embedding = await self.embedding_service.encode_single(query)

        # Search vector store
        results = await self.vector_store.search(
            collection_name="knowledge_base_documents",
            query_embedding=query_embedding,
            top_k=top_k,
            where=filters,
        )

        # Format results
        search_results = []
        for i, chunk_id in enumerate(results["ids"][0]):
            relevance_score = 1.0 - results["distances"][0][i]  # Convert distance to similarity

            if relevance_score < min_relevance:
                continue

            metadata = results["metadatas"][0][i]
            chunk_text = results["documents"][0][i]

            search_results.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": metadata.get("document_id"),
                    "filename": metadata.get("filename"),
                    "chunk_text": chunk_text,
                    "relevance_score": relevance_score,
                    "chunk_index": metadata.get("chunk_index"),
                    "format": metadata.get("format"),
                    "processing_method": metadata.get("processing_method"),
                }
            )

        logger.info(f"Search query '{query[:50]}...' returned {len(search_results)} results")

        return search_results

    async def remove_document(self, document_id: str) -> bool:
        """
        Remove a document from the knowledge base.

        Args:
            document_id: ID of document to remove

        Returns:
            True if document was removed, False if not found
        """
        document = self._documents.get(document_id)
        if not document:
            logger.warning(f"Document not found: {document_id}")
            return False

        # Remove embeddings from vector store
        collection = self.vector_store.get_or_create_collection("knowledge_base_documents")
        if document.embedding_ids:
            collection.delete(ids=document.embedding_ids)
            logger.info(f"Removed {len(document.embedding_ids)} embeddings")

        # Remove document
        del self._documents[document_id]
        logger.info(f"Removed document: {document.filename}")

        return True

    async def clear_knowledge_base(self) -> int:
        """
        Clear all documents from the knowledge base.

        Returns:
            Number of documents removed
        """
        count = len(self._documents)

        # Reset vector store
        self.vector_store.reset()

        # Clear documents
        self._documents.clear()
        self._tasks.clear()

        logger.info(f"Cleared knowledge base: {count} documents removed")

        return count

    def get_statistics(self) -> dict[str, Any]:
        """
        Get knowledge base statistics.

        Returns:
            Dictionary with statistics
        """
        total_chunks = sum(doc.chunk_count for doc in self._documents.values())
        total_size = sum(doc.size_bytes for doc in self._documents.values())

        completed = [
            d for d in self._documents.values() if d.processing_status == ProcessingStatus.COMPLETED
        ]
        failed = [
            d for d in self._documents.values() if d.processing_status == ProcessingStatus.FAILED
        ]

        return {
            "document_count": len(self._documents),
            "total_chunks": total_chunks,
            "total_size_mb": total_size / (1024 * 1024),
            "average_chunks_per_document": (
                total_chunks / len(self._documents) if self._documents else 0
            ),
            "completed": len(completed),
            "failed": len(failed),
            "formats": {
                fmt.value: sum(1 for d in self._documents.values() if d.format == fmt)
                for fmt in DocumentFormat
            },
        }
