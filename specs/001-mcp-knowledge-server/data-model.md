# Data Model: MCP Knowledge Server

**Date**: 2025-10-26  
**Feature**: MCP Knowledge Server  
**Phase**: 1 - Design

## Overview

This document defines the core entities, their relationships, and state transitions for the MCP Knowledge Server.

## Core Entities

### 1. Document

Represents a file added to the knowledge base with all associated metadata.

**Attributes**:
- `id: str` - Unique identifier (UUID)
- `filename: str` - Original filename
- `file_path: str` - Path to original file in storage
- `content_hash: str` - SHA-256 hash of file content (for deduplication)
- `format: DocumentFormat` - File format enum (PDF, DOCX, PPTX, XLSX, HTML, JPG, PNG, SVG)
- `size_bytes: int` - File size in bytes
- `date_added: datetime` - When document was added to knowledge base
- `date_modified: datetime` - When document was last modified
- `processing_status: ProcessingStatus` - Current processing state
- `processing_method: ProcessingMethod` - How content was extracted (TEXT_EXTRACTION, OCR, HYBRID)
- `chunk_count: int` - Number of chunks generated
- `embedding_ids: List[str]` - IDs of embeddings in vector database
- `metadata: Dict[str, Any]` - Additional metadata (author, title, page count, etc.)
- `error_message: Optional[str]` - Error message if processing failed

**Enums**:

```python
class DocumentFormat(Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    HTML = "html"
    JPG = "jpg"
    PNG = "png"
    SVG = "svg"

class ProcessingStatus(Enum):
    PENDING = "pending"           # Queued for processing
    PROCESSING = "processing"     # Currently being processed
    COMPLETED = "completed"       # Successfully processed
    FAILED = "failed"            # Processing failed
    PARTIAL = "partial"          # Partially processed (some chunks failed)

class ProcessingMethod(Enum):
    TEXT_EXTRACTION = "text_extraction"  # Direct text from document
    OCR = "ocr"                          # OCR applied
    HYBRID = "hybrid"                    # Combination of both
    IMAGE_ANALYSIS = "image_analysis"    # Image content analysis
```

**Validation Rules**:
- `filename`: Non-empty, valid characters only
- `file_path`: Must exist in storage directory
- `format`: Must match file extension
- `size_bytes`: Must be > 0 and <= max_file_size_mb (config)
- `chunk_count`: >= 0
- `embedding_ids`: Length must equal chunk_count when processing complete

**State Transitions**:
```
PENDING → PROCESSING → COMPLETED
              ↓
           FAILED
              ↓
           PARTIAL
```

**Relationships**:
- Document has many Embeddings (1:N)
- Document belongs to one KnowledgeBase (N:1)

---

### 2. Embedding

Represents a vector embedding of a document chunk with context.

**Attributes**:
- `id: str` - Unique identifier (UUID)
- `document_id: str` - Reference to parent Document
- `chunk_index: int` - Position of this chunk in document (0-indexed)
- `chunk_text: str` - The text that was embedded
- `vector: List[float]` - Embedding vector (384 dimensions for all-MiniLM-L6-v2)
- `metadata: Dict[str, Any]` - Chunk metadata (start_pos, end_pos, page_num, etc.)
- `created_at: datetime` - When embedding was created

**Validation Rules**:
- `document_id`: Must reference existing Document
- `chunk_index`: >= 0, must be unique per document
- `chunk_text`: Non-empty, <= max_chunk_size (config)
- `vector`: Length must be 384 (model dimensionality)
- `metadata`: Must contain source document context

**Storage**:
- Vectors stored in ChromaDB
- Metadata stored alongside for filtering
- Full text searchable via metadata

**Relationships**:
- Embedding belongs to one Document (N:1)

---

### 3. SearchResult

Represents a single result from a semantic search query.

**Attributes**:
- `document_id: str` - ID of source document
- `chunk_id: str` - ID of matching embedding/chunk
- `chunk_text: str` - The matching text excerpt
- `relevance_score: float` - Similarity score (0.0 to 1.0, higher is better)
- `document_metadata: Dict[str, Any]` - Document filename, format, date added
- `chunk_metadata: Dict[str, Any]` - Chunk position, page number, etc.
- `highlight: Optional[str]` - Text with query terms highlighted (future enhancement)

**Validation Rules**:
- `relevance_score`: 0.0 <= score <= 1.0
- `chunk_text`: Non-empty
- `document_id` and `chunk_id`: Must reference existing entities

**Relationships**:
- SearchResult references one Document (N:1)
- SearchResult references one Embedding (N:1)

---

### 4. KnowledgeBase

Represents the aggregate of all documents and embeddings with statistics.

**Attributes**:
- `id: str` - Knowledge base identifier (typically "default" for single KB)
- `name: str` - Human-readable name
- `document_count: int` - Total number of documents
- `embedding_count: int` - Total number of embeddings/chunks
- `total_size_bytes: int` - Sum of all document sizes
- `storage_path: str` - Path to storage directory
- `vector_db_path: str` - Path to ChromaDB storage
- `created_at: datetime` - When knowledge base was created
- `last_updated: datetime` - When last document was added/removed
- `configuration: Dict[str, Any]` - KB-specific configuration

**Computed Properties**:
- `average_chunks_per_document: float` - embedding_count / document_count
- `storage_size_mb: float` - total_size_bytes / (1024 * 1024)

**Validation Rules**:
- `name`: Non-empty
- `document_count`: >= 0
- `embedding_count`: >= 0
- `storage_path` and `vector_db_path`: Must be valid directories

**Operations**:
- `add_document(document: Document)` - Add document and update stats
- `remove_document(document_id: str)` - Remove document and update stats
- `clear()` - Remove all documents and embeddings
- `get_statistics()` - Return summary statistics

**Relationships**:
- KnowledgeBase has many Documents (1:N)

---

### 5. ProcessingStrategy

Represents the decision logic for how to process a document (OCR vs text extraction).

**Attributes**:
- `document_format: DocumentFormat` - Type of document
- `has_text_layer: bool` - Whether document has extractable text
- `extracted_text_length: int` - Length of extracted text (if any)
- `confidence_score: float` - Confidence in text extraction quality
- `recommended_method: ProcessingMethod` - Recommended processing approach

**Decision Logic**:

```python
def determine_processing_method(document: Document) -> ProcessingMethod:
    if document.format in [JPG, PNG, SVG]:
        return ProcessingMethod.IMAGE_ANALYSIS
    
    # Try text extraction first
    extracted_text = extract_text(document)
    
    if len(extracted_text) < 100:
        # Too little text, likely scanned
        return ProcessingMethod.OCR
    
    if is_gibberish(extracted_text):
        # Text extraction failed, try OCR
        return ProcessingMethod.OCR
    
    if has_embedded_images(document):
        # Use both methods
        return ProcessingMethod.HYBRID
    
    return ProcessingMethod.TEXT_EXTRACTION
```

**Validation Rules**:
- `extracted_text_length`: >= 0
- `confidence_score`: 0.0 <= score <= 1.0

---

### 6. ProcessingTask

Represents an async document processing task with progress tracking.

**Attributes**:
- `task_id: str` - Unique task identifier (UUID)
- `document_id: str` - Document being processed
- `status: TaskStatus` - Current task status
- `progress: float` - Progress percentage (0.0 to 1.0)
- `current_step: str` - Description of current step
- `total_steps: int` - Estimated total steps
- `completed_steps: int` - Number of completed steps
- `started_at: datetime` - When task started
- `completed_at: Optional[datetime]` - When task finished
- `error: Optional[str]` - Error message if failed

**Enums**:

```python
class TaskStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**State Transitions**:
```
QUEUED → RUNNING → COMPLETED
            ↓
         FAILED
            ↓
        CANCELLED
```

**Validation Rules**:
- `progress`: 0.0 <= progress <= 1.0
- `completed_steps`: <= total_steps
- `completed_at`: Must be after started_at if set

---

## Relationships Diagram

```
KnowledgeBase (1) ──────── (N) Document (1) ──────── (N) Embedding
                                    │
                                    │ references
                                    ↓
                              SearchResult ←─ references ─→ Embedding
                                    
ProcessingTask (N) ──references──→ Document (1)

ProcessingStrategy ──analyzes──→ Document (1)
```

## Data Persistence

### ChromaDB Schema

**Collection**: `knowledge_base_documents`

Each document's chunks stored as:
```python
{
    "ids": ["chunk_uuid_1", "chunk_uuid_2", ...],
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],
    "metadatas": [
        {
            "document_id": "doc_uuid",
            "filename": "example.pdf",
            "chunk_index": 0,
            "chunk_text": "...",
            "format": "pdf",
            "page_num": 1,
            "processing_method": "text_extraction",
            "date_added": "2025-10-26T10:00:00Z"
        },
        ...
    ],
    "documents": ["chunk text 1", "chunk text 2", ...]  # Full text for reference
}
```

**Indexes**:
- Vector index (HNSW) for similarity search
- Metadata filters on: `document_id`, `filename`, `format`, `date_added`

### Filesystem Storage

**Document Storage**:
```
{storage_path}/
├── documents/
│   ├── {document_id}/
│   │   ├── original.{ext}       # Original file
│   │   ├── metadata.json        # Document metadata
│   │   └── extracted_text.txt   # Extracted text (optional)
└── metadata.db                  # SQLite for document metadata (optional)
```

**Vector Database Storage**:
```
{vector_db_path}/
└── chroma.sqlite3              # ChromaDB persistent storage
```

## Data Access Patterns

### Common Queries

1. **Add Document**:
   - Validate and store file
   - Extract text/OCR
   - Chunk text
   - Generate embeddings
   - Store in ChromaDB
   - Update KnowledgeBase stats

2. **Search**:
   - Generate query embedding
   - Query ChromaDB for similar vectors
   - Retrieve top N results
   - Hydrate with document metadata
   - Return SearchResults

3. **Remove Document**:
   - Get document embedding IDs
   - Delete embeddings from ChromaDB
   - Delete document files
   - Update KnowledgeBase stats

4. **List Documents**:
   - Query all documents from ChromaDB metadata
   - Group by document_id
   - Return document metadata

5. **Get Status**:
   - Count documents in ChromaDB
   - Sum storage sizes
   - Return statistics

## Data Validation

### Input Validation

- File format matches extension
- File size within limits (< 100MB default)
- File is readable and not corrupted
- Filename contains no path traversal characters

### Output Validation

- Embeddings have correct dimensionality (384)
- All chunks have valid document references
- Metadata is complete and well-formed
- State transitions are valid

## Migration Strategy

### Version 1.0 Schema

Current schema as defined above.

### Future Versions

- Add `schema_version` to metadata
- Implement migration scripts for schema changes
- Maintain backward compatibility for 1 major version

### Data Export/Import

Support export to JSON format:
```json
{
  "version": "1.0",
  "knowledge_base": {...},
  "documents": [...],
  "embeddings": [...]
}
```

## Performance Considerations

### Indexing Performance

- Batch insert embeddings (32-64 at a time)
- Async processing to avoid blocking
- Progress tracking every 10 chunks

### Query Performance

- ChromaDB HNSW index for fast similarity search
- Metadata filters before vector search (if applicable)
- Limit results to top 10-20 for UI responsiveness

### Storage Optimization

- Compress original documents (optional)
- Store only essential metadata
- Periodic cleanup of orphaned embeddings

## Testing Data Requirements

### Unit Tests

- Mock documents with known embeddings
- Test data validation edge cases
- Test state transitions

### Integration Tests

- Sample documents: PDF (10 pages), DOCX (5 pages), scanned PDF, image
- Test with 100+ documents for performance
- Test concurrent operations

### Performance Tests

- 1000+ documents for search latency testing
- Large documents (100+ pages) for memory profiling
- Concurrent operations (10+ clients)
