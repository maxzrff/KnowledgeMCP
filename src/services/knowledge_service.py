"""
Core knowledge service for document management.
"""

import asyncio
import hashlib
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from src.config.settings import get_settings
from src.models.document import (
    Document,
    DocumentFormat,
    ProcessingStatus,
    ProcessingTask,
    TaskStatus,
)
from src.services.context_service import ContextService
from src.services.embedding_service import EmbeddingService
from src.services.text_extractor import TextExtractor
from src.services.vector_store import VectorStore
from src.utils.chunking import chunk_text
from src.utils.logging_config import get_logger
from src.utils.validation import validate_file_exists, validate_file_format, validate_file_size

logger = get_logger(__name__)


class KnowledgeService:
    """Core service for knowledge base operations with multi-context support."""

    def __init__(self):
        self.settings = get_settings()
        self.context_service = ContextService()
        self.text_extractor = TextExtractor(
            force_ocr=self.settings.ocr.force_ocr,
            ocr_language=self.settings.ocr.language,
        )
        self.embedding_service = EmbeddingService(
            model_name=self.settings.embedding.model_name,
            device=self.settings.embedding.device,
            cache_folder=self.settings.storage.model_cache_path,
        )
        self.vector_store = VectorStore(self.settings.storage.vector_db_path)
        self._tasks: dict[str, ProcessingTask] = {}
        self._documents: dict[str, Document] = {}
        self._load_existing_documents()

    def _load_existing_documents(self):
        """Load existing documents from vector store on initialization."""
        try:
            # Get all unique document IDs from vector store
            all_data = self.vector_store.get_all_documents()
            
            # Group by document_id to reconstruct Document objects
            doc_map = {}
            for metadata in all_data.get("metadatas", []):
                doc_id = metadata.get("document_id")
                if not doc_id or doc_id in doc_map:
                    continue
                    
                doc_map[doc_id] = metadata
            
            # Recreate Document objects
            for doc_id, metadata in doc_map.items():
                # Count chunks for this document
                chunk_count = sum(1 for m in all_data.get("metadatas", []) if m.get("document_id") == doc_id)
                
                # Get size_bytes, use 1 as default to pass validation (actual size unknown for old data)
                size_bytes = metadata.get("size_bytes")
                if not size_bytes or size_bytes == 0:
                    size_bytes = 1  # Placeholder for legacy data
                
                # Reconstruct document
                doc = Document(
                    id=doc_id,
                    filename=metadata.get("filename", "unknown"),
                    file_path=metadata.get("file_path", ""),
                    content_hash=metadata.get("content_hash", ""),
                    format=DocumentFormat(metadata.get("format", "pdf")),
                    size_bytes=size_bytes,
                    metadata={},
                    processing_status=ProcessingStatus.COMPLETED,
                    chunk_count=chunk_count,
                )
                self._documents[doc_id] = doc
                
            if self._documents:
                logger.info(f"Loaded {len(self._documents)} existing documents from vector store")
        except Exception as e:
            logger.warning(f"Could not load existing documents: {e}")

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
        force_ocr: bool = False,
        contexts: list[str] | None = None,
    ) -> str:
        """
        Add a document to the knowledge base.

        Args:
            file_path: Path to the document file
            metadata: Optional metadata dictionary
            async_processing: If True, process asynchronously and return task ID
            force_ocr: Force OCR even if text extraction is available
            contexts: List of context names to add document to (default: ["default"])

        Returns:
            Task ID if async, document ID if sync
        """
        # Default to ["default"] if no contexts specified
        if not contexts:
            contexts = ["default"]
        
        # Validate all contexts exist
        for ctx in contexts:
            if not self.context_service.context_exists(ctx):
                raise ValueError(f"Context '{ctx}' does not exist")
        
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

        # Create document with contexts
        document = Document(
            filename=file_path.name,
            file_path=str(file_path),
            content_hash=content_hash,
            format=document_format,
            size_bytes=file_path.stat().st_size,
            contexts=contexts,
            metadata=metadata or {},
        )

        self._documents[document.id] = document

        if async_processing:
            # Create async task
            task = ProcessingTask(document_id=document.id, total_steps=4)
            self._tasks[task.task_id] = task

            # Start processing in background
            asyncio.create_task(
                self._process_document_async(task.task_id, document, force_ocr)
            )

            logger.info(f"Document queued for async processing: {file_path.name}")
            return task.task_id
        # Process synchronously
        await self._process_document(document, force_ocr)
        return document.id

    async def _process_document_async(self, task_id: str, document: Document, force_ocr: bool = False) -> None:
        """Process document asynchronously with progress tracking."""
        task = self._tasks[task_id]
        task.status = TaskStatus.RUNNING

        try:
            task.current_step = "Extracting text"
            task.completed_steps = 1
            task.progress = 0.25

            await self._process_document(document, force_ocr)

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

    async def _process_document(self, document: Document, force_ocr: bool = False) -> None:
        """Process a single document."""
        document.processing_status = ProcessingStatus.PROCESSING

        # Temporarily override force_ocr setting if requested
        original_force_ocr = self.text_extractor.ocr_service.force_ocr
        if force_ocr:
            self.text_extractor.ocr_service.force_ocr = True

        try:
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

            # Store in vector database - add to each context
            for context in document.contexts:
                # Create unique embedding IDs per context
                context_embedding_ids = [f"{context}_{str(uuid4())}" for _ in chunks]
                
                context_metadatas = []
                for i in range(len(chunks)):
                    context_metadatas.append(
                        {
                            "document_id": document.id,
                            "filename": document.filename,
                            "file_path": document.file_path,
                            "content_hash": document.content_hash,
                            "size_bytes": document.size_bytes,
                            "chunk_index": i,
                            "format": document.format.value,
                            "context": context,
                            "processing_method": (
                                document.processing_method.value
                                if document.processing_method
                                else "unknown"
                            ),
                        }
                    )
                
                # Add to vector store for this context
                await self.vector_store.add_embeddings(
                    collection_name="knowledge_base_documents",  # Legacy parameter
                    ids=context_embedding_ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=context_metadatas,
                    context=context,
                )
                
                # Update context document count
                try:
                    self.context_service.increment_document_count(context)
                except Exception as e:
                    logger.warning(f"Could not update document count for context '{context}': {e}")

            # Update document
            document.chunk_count = len(chunks)
            document.processing_status = ProcessingStatus.COMPLETED

            logger.info(
                f"Document processed: {document.filename} - "
                f"{len(chunks)} chunks in contexts: {', '.join(document.contexts)}"
            )
        finally:
            # Restore original force_ocr setting
            if force_ocr:
                self.text_extractor.ocr_service.force_ocr = original_force_ocr

    def get_task_status(self, task_id: str) -> ProcessingTask | None:
        """Get status of processing task."""
        return self._tasks.get(task_id)

    def list_documents(self, context: str | None = None) -> list[Document]:
        """
        List all documents in knowledge base.
        
        Args:
            context: Optional context filter (None = all documents)
            
        Returns:
            List of Document objects
        """
        if context:
            # Filter documents by context
            return [doc for doc in self._documents.values() if context in doc.contexts]
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
        context: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search the knowledge base using natural language query.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            min_relevance: Minimum relevance score threshold
            filters: Optional metadata filters
            context: Optional context name (None = search all contexts)

        Returns:
            List of search results with relevance scores
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Generate query embedding
        query_embedding = await self.embedding_service.encode_single(query)

        # Search vector store (context-aware)
        results = await self.vector_store.search(
            collection_name="knowledge_base_documents",
            query_embedding=query_embedding,
            top_k=top_k,
            where=filters,
            context=context,
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
                    "context": metadata.get("context"),
                    "processing_method": metadata.get("processing_method"),
                }
            )

        context_info = f" in context '{context}'" if context else " across all contexts"
        logger.info(f"Search query '{query[:50]}...'{context_info} returned {len(search_results)} results")

        return search_results

    async def remove_document(self, document_id: str) -> bool:
        """
        Remove a document from the knowledge base and all contexts.

        Args:
            document_id: ID of document to remove

        Returns:
            True if document was removed, False if not found
        """
        document = self._documents.get(document_id)
        if not document:
            logger.warning(f"Document not found: {document_id}")
            return False

        # Remove embeddings from each context
        for context in document.contexts:
            try:
                collection = self.vector_store.get_collection(context)
                # Get all embeddings for this document in this context
                results = collection.get(where={"document_id": document_id})
                if results and results.get("ids"):
                    embedding_ids = results["ids"]
                    collection.delete(ids=embedding_ids)
                    logger.info(f"Removed {len(embedding_ids)} embeddings for document {document_id} from context '{context}'")
                
                # Update context document count
                try:
                    self.context_service.decrement_document_count(context)
                except Exception as e:
                    logger.warning(f"Could not update document count for context '{context}': {e}")
            except Exception as e:
                logger.error(f"Error removing embeddings for document {document_id} from context '{context}': {e}")

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

    def create_context(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ):
        """
        Create a new context.
        
        Args:
            name: Unique context name
            description: Optional description
            metadata: Optional metadata dictionary
            
        Returns:
            Created Context object
        """
        return self.context_service.create_context(name, description, metadata)

    def list_contexts(self):
        """
        List all contexts.
        
        Returns:
            List of Context objects
        """
        return self.context_service.list_contexts()

    def get_context(self, name: str):
        """
        Get a specific context by name.
        
        Args:
            name: Context name
            
        Returns:
            Context object
        """
        return self.context_service.get_context(name)

    def delete_context(self, name: str) -> str:
        """
        Delete a context.
        
        Args:
            name: Context name to delete
            
        Returns:
            Success message
        """
        # Remove from ChromaDB
        try:
            self.vector_store.delete_collection(name)
        except Exception as e:
            logger.warning(f"Could not delete ChromaDB collection {name}: {e}")
        
        # Remove from context service
        return self.context_service.delete_context(name)

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
