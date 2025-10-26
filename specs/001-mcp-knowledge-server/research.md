# Research: MCP Knowledge Server

**Date**: 2025-10-26  
**Feature**: MCP Knowledge Server  
**Phase**: 0 - Research & Technology Selection

## Overview

This document consolidates research findings for key technology decisions and implementation patterns for the MCP Knowledge Server.

## Technology Decisions

### 1. Vector Database: ChromaDB

**Decision**: Use ChromaDB as the vector database for semantic search

**Rationale**:
- **Simplicity**: Embedded database with no separate server process needed
- **Python-native**: First-class Python support with clean API
- **Persistent storage**: Built-in persistence to local filesystem
- **Performance**: Efficient similarity search with HNSW indexing
- **Metadata support**: Store document metadata alongside embeddings
- **Active development**: Well-maintained with good documentation

**Alternatives Considered**:
- **Faiss**: More complex setup, requires separate metadata storage
- **Qdrant**: Requires separate server process, adds deployment complexity
- **Pinecone**: Cloud-only, doesn't meet local storage requirement
- **Weaviate**: Heavier weight, requires Docker/separate service

**Implementation Notes**:
- Use persistent client with configurable storage path
- Collection per knowledge base for isolation
- Metadata filtering for efficient document removal
- Distance metric: cosine similarity for semantic search

### 2. Embedding Model: all-MiniLM-L6-v2

**Decision**: Use sentence-transformers all-MiniLM-L6-v2 model

**Rationale**:
- **Size**: Only 80MB - fast download and caching
- **Performance**: Good balance of speed and quality (384 dimensions)
- **Speed**: Fast inference (~1000 sentences/sec on CPU)
- **Quality**: Strong semantic understanding for general text
- **Caching**: Sentence-transformers supports local model caching
- **No API calls**: Fully local, no rate limits or timeouts

**Alternatives Considered**:
- **all-mpnet-base-v2**: Better quality but slower (768 dimensions)
- **OpenAI embeddings**: Requires API calls, cost and latency concerns
- **Cohere embeddings**: Same API concerns as OpenAI
- **BERT variants**: Larger models, slower inference

**Implementation Notes**:
- Cache model in `~/.cache/huggingface/` or custom path
- Check cache before first use, download if needed with retry logic
- Batch embedding generation for efficiency (32-64 documents per batch)
- Normalize embeddings for cosine similarity

### 3. Document Processing Libraries

**Decision**: Use specialized libraries per format

**PDF Processing**:
- **Primary**: pdfplumber (better text extraction, preserves layout)
- **Fallback**: PyPDF2 (simpler, faster for basic PDFs)
- **Rationale**: pdfplumber handles complex layouts better, PyPDF2 as fallback

**DOCX Processing**:
- **Library**: python-docx
- **Rationale**: Official Microsoft format support, stable API

**PPTX Processing**:
- **Library**: python-pptx
- **Rationale**: Same ecosystem as python-docx, good slide extraction

**XLSX Processing**:
- **Library**: openpyxl
- **Rationale**: Full XLSX support, preserves cell structure

**HTML Processing**:
- **Library**: beautifulsoup4 + lxml parser
- **Rationale**: Robust HTML parsing, good text extraction

**Image Processing**:
- **Library**: Pillow (PIL)
- **Rationale**: Standard Python imaging library, format conversion support

### 4. OCR Engine: Tesseract

**Decision**: Use pytesseract wrapper for Tesseract OCR

**Rationale**:
- **Open source**: Free, no API costs
- **Local processing**: No external dependencies
- **Multi-language**: Supports 100+ languages
- **Mature**: Stable, well-tested
- **Integration**: Clean Python wrapper

**Alternatives Considered**:
- **Cloud OCR (Google, AWS)**: API costs, latency, privacy concerns
- **EasyOCR**: Slower, larger models
- **PaddleOCR**: Less mature Python support

**Implementation Notes**:
- Preprocess images (grayscale, contrast adjustment) before OCR
- Use page segmentation mode PSM_AUTO
- Language hint: English (configurable)
- Confidence threshold: 60% (reject low-confidence extractions)

### 5. MCP Protocol Implementation

**Decision**: Use official MCP Python SDK with custom HTTP streaming transport

**Rationale**:
- **Official SDK**: Follows specification exactly (2025-06-18)
- **Type safety**: Full type hints for tool definitions
- **Streaming support**: Built-in support for streaming transport
- **Extensibility**: Easy to implement custom transports

**MCP Specification Compliance**:
- Tool schema definitions with typed parameters
- Error handling with proper error codes
- Progress notifications for long-running operations
- Cancellation support for background tasks

**HTTP Transport**:
- **Library**: aiohttp (async HTTP server)
- **Alternative**: FastAPI could be used if REST API needed later
- **Rationale**: aiohttp is lightweight, perfect for streaming transport

**Implementation Notes**:
- SSE (Server-Sent Events) for server-to-client streaming
- JSON-RPC 2.0 message format
- WebSocket as alternative transport option
- Connection pooling for concurrent clients

### 6. Async Processing Architecture

**Decision**: Use asyncio with background task queue

**Rationale**:
- **Non-blocking**: MCP calls return immediately with task ID
- **Progress tracking**: Periodic progress updates via MCP notifications
- **Concurrency**: Handle multiple document processing simultaneously
- **Resource control**: Limit concurrent processing to avoid memory issues

**Implementation Pattern**:
```python
# Async processing pattern
async def add_document(file_path: str) -> str:
    task_id = generate_task_id()
    asyncio.create_task(process_document_async(task_id, file_path))
    return task_id

async def process_document_async(task_id: str, file_path: str):
    total_steps = estimate_steps(file_path)
    for step in range(total_steps):
        # Process chunk
        await notify_progress(task_id, step / total_steps)
    await notify_complete(task_id)
```

**Libraries**:
- asyncio (standard library)
- aiofiles for async file I/O
- asyncio.Queue for task management

### 7. Configuration Management

**Decision**: YAML configuration with environment variable overrides

**Rationale**:
- **Readability**: YAML is human-readable
- **Flexibility**: Environment variables for deployment-specific settings
- **Validation**: Pydantic models for type-safe configuration

**Configuration Structure**:
```yaml
storage:
  documents_path: ./data/documents
  vector_db_path: ./data/chromadb
  model_cache_path: ~/.cache/huggingface

embedding:
  model_name: sentence-transformers/all-MiniLM-L6-v2
  batch_size: 32
  device: cpu  # or cuda

chunking:
  chunk_size: 500  # tokens
  chunk_overlap: 50  # tokens
  strategy: sentence  # sentence, paragraph, fixed

processing:
  max_concurrent_tasks: 3
  ocr_confidence_threshold: 0.6
  max_file_size_mb: 100

mcp:
  host: 0.0.0.0
  port: 3000
  transport: http  # or websocket
```

## Best Practices

### 1. Text Chunking Strategy

**Decision**: Sentence-aware chunking with overlap

**Rationale**:
- Preserves semantic boundaries (don't split mid-sentence)
- Overlap ensures context continuity
- Token-based sizing for consistent embedding quality

**Implementation**:
- Use sentence tokenizer (NLTK or spaCy)
- Target 500-1000 tokens per chunk
- 10% overlap between chunks
- Store chunk position and source document reference

### 2. OCR vs Text Extraction Decision Logic

**Decision**: Automatic detection with fallback strategy

**Detection Logic**:
1. Try text extraction first
2. If extracted text < 100 characters → likely scanned → try OCR
3. If text extraction errors → try OCR
4. If both fail → log error, store metadata only

**Heuristics**:
- PDF: Check for embedded text layer
- Images: Always use OCR
- Documents: Text extraction first

### 3. Duplicate Document Handling

**Decision**: Content-based deduplication with hash

**Strategy**:
- Calculate SHA-256 hash of file content
- Check hash before processing
- If duplicate: update metadata, skip re-embedding
- If filename different but content same: create alias

### 4. Error Handling Strategy

**Principles**:
- Fail gracefully: Partial failures don't block entire operation
- Clear messages: Include file path, error type, suggested action
- Retry logic: Transient errors (network, temp files) get 3 retries
- Logging: All errors logged with context

**Example Error Messages**:
- ❌ Bad: "Error processing file"
- ✅ Good: "Failed to extract text from document.pdf: File appears to be password-protected. Remove password and try again."

### 5. Performance Optimization

**Strategies**:
- **Batch processing**: Process multiple documents in parallel (limit 3-5)
- **Lazy loading**: Load models only when needed
- **Caching**: Cache embedding model, preprocessed images
- **Streaming**: Stream large documents instead of loading fully into memory
- **Database indexing**: Metadata fields indexed in ChromaDB for fast filtering

**Memory Management**:
- Process documents in streaming mode (chunks)
- Clear memory after each document
- Monitor memory usage, pause if threshold exceeded
- Garbage collection after batch processing

### 6. Testing Strategy

**Unit Tests**:
- Mock external dependencies (ChromaDB, model inference)
- Test each document processor independently
- Test chunking logic with edge cases
- Test OCR detection heuristics

**Integration Tests**:
- End-to-end workflows (add → search → remove)
- Test with real documents (PDF, DOCX samples)
- Test async processing and progress tracking
- Test MCP protocol compliance

**Contract Tests**:
- Verify MCP tool schemas
- Test tool parameter validation
- Test error responses match MCP spec

**Performance Tests**:
- Measure indexing throughput (target: 50-100 chunks/sec)
- Measure search latency with varying document counts
- Memory profiling with large document sets

## Security Considerations

1. **File Validation**: Validate file formats before processing (prevent malicious files)
2. **Path Traversal**: Sanitize file paths, restrict to allowed directories
3. **Resource Limits**: Max file size (100MB), max processing time (5 min)
4. **Dependency Scanning**: Regular security audits of dependencies
5. **No External Calls**: All processing local (no data leaves system)

## Migration & Compatibility

**Forward Compatibility**:
- Version metadata in ChromaDB collections
- Schema migrations for database updates
- Backward-compatible configuration with defaults

**MCP Client Compatibility**:
- Tested with: Claude Desktop, GitHub Copilot, Amazon Q CLI
- Standard MCP protocol ensures broad compatibility
- Transport negotiation (HTTP, WebSocket)

## Open Questions & Future Enhancements

**Resolved in This Plan**:
- ✅ Vector database choice → ChromaDB
- ✅ Embedding model → all-MiniLM-L6-v2
- ✅ OCR engine → Tesseract
- ✅ Document processing libraries → Specialized per format
- ✅ Async architecture → asyncio with task queue
- ✅ Configuration approach → YAML + environment variables

**Future Enhancements** (out of scope for v1):
- Multi-language support (currently English-focused)
- Custom embedding models (user-provided)
- Cloud vector database integration (Pinecone, Weaviate)
- Incremental re-indexing (update changed documents only)
- Query expansion and relevance feedback
- Document versioning and history tracking

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [MCP Specification 2025-06-18](https://modelcontextprotocol.io/specification)
- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)
- [Python asyncio Best Practices](https://docs.python.org/3/library/asyncio.html)
