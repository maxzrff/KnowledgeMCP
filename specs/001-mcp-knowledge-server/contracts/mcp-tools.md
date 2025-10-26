# MCP Tool Contracts: Knowledge Server

**Date**: 2025-10-26  
**Feature**: MCP Knowledge Server  
**Phase**: 1 - Design  
**MCP Specification**: 2025-06-18

## Overview

This document defines the MCP tool contracts for the Knowledge Server. All tools follow the MCP specification for tool definitions, parameter schemas, and response formats.

## Tool Definitions

### 1. knowledge-add

**Description**: Add a document or image to the knowledge base for semantic search

**Parameters**:

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `file_path` | string | Yes | Path to the document or image file | Must exist, readable, supported format |
| `metadata` | object | No | Additional metadata (author, title, tags) | Valid JSON object |
| `force_ocr` | boolean | No | Force OCR even if text extraction available | Default: false |
| `async` | boolean | No | Process asynchronously and return task ID | Default: true |

**Supported Formats**: PDF, DOCX, PPTX, XLSX, HTML, JPG, PNG, SVG

**Response (Async)**:

```json
{
  "success": true,
  "task_id": "uuid-v4-task-id",
  "message": "Document queued for processing",
  "estimated_time_seconds": 30
}
```

**Response (Sync)**:

```json
{
  "success": true,
  "document_id": "uuid-v4-document-id",
  "filename": "example.pdf",
  "chunks_created": 45,
  "processing_method": "text_extraction",
  "processing_time_seconds": 12.5
}
```

**Error Responses**:

```json
{
  "success": false,
  "error": "unsupported_format",
  "message": "Unsupported file format: .xyz. Use PDF, DOCX, PPTX, XLSX, HTML, JPG, PNG, or SVG",
  "supported_formats": ["pdf", "docx", "pptx", "xlsx", "html", "jpg", "png", "svg"]
}
```

```json
{
  "success": false,
  "error": "file_too_large",
  "message": "File size (150 MB) exceeds maximum allowed size (100 MB)",
  "max_size_mb": 100
}
```

**Example Usage**:

```json
{
  "tool": "knowledge-add",
  "parameters": {
    "file_path": "/path/to/document.pdf",
    "metadata": {
      "author": "John Doe",
      "tags": ["technical", "api-docs"]
    },
    "async": true
  }
}
```

---

### 2. knowledge-search

**Description**: Search the knowledge base using natural language query

**Parameters**:

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `query` | string | Yes | Natural language search query | Non-empty, max 500 chars |
| `top_k` | integer | No | Number of results to return | Default: 10, max: 50 |
| `min_relevance` | float | No | Minimum relevance score (0.0 to 1.0) | Default: 0.0 |
| `filters` | object | No | Metadata filters (format, date_range) | Valid filter object |

**Response**:

```json
{
  "success": true,
  "query": "How to configure authentication?",
  "results": [
    {
      "document_id": "uuid-v4-doc-id",
      "chunk_id": "uuid-v4-chunk-id",
      "filename": "auth-guide.pdf",
      "chunk_text": "To configure authentication, first set up the OAuth2 provider...",
      "relevance_score": 0.89,
      "metadata": {
        "format": "pdf",
        "page_num": 5,
        "date_added": "2025-10-26T10:00:00Z"
      }
    }
  ],
  "total_results": 1,
  "search_time_ms": 125
}
```

**Empty Results**:

```json
{
  "success": true,
  "query": "non-existent topic",
  "results": [],
  "total_results": 0,
  "message": "No documents found matching your query",
  "search_time_ms": 50
}
```

**Error Responses**:

```json
{
  "success": false,
  "error": "empty_knowledge_base",
  "message": "Knowledge base is empty. Add documents with knowledge-add first",
  "document_count": 0
}
```

**Example Usage**:

```json
{
  "tool": "knowledge-search",
  "parameters": {
    "query": "How to set up vector database?",
    "top_k": 5,
    "min_relevance": 0.5,
    "filters": {
      "format": "pdf",
      "date_range": {
        "start": "2025-01-01",
        "end": "2025-12-31"
      }
    }
  }
}
```

---

### 3. knowledge-remove

**Description**: Remove a specific document from the knowledge base

**Parameters**:

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `document_id` | string | Yes | ID of document to remove | Must exist |
| `confirm` | boolean | No | Confirmation flag for safety | Default: false |

**Response**:

```json
{
  "success": true,
  "document_id": "uuid-v4-doc-id",
  "filename": "old-document.pdf",
  "chunks_removed": 45,
  "message": "Document removed successfully"
}
```

**Confirmation Required**:

```json
{
  "success": false,
  "error": "confirmation_required",
  "message": "Set confirm=true to remove this document",
  "document": {
    "id": "uuid-v4-doc-id",
    "filename": "important.pdf",
    "chunks": 45
  }
}
```

**Error Responses**:

```json
{
  "success": false,
  "error": "document_not_found",
  "message": "Document with ID 'uuid-v4-doc-id' not found",
  "document_id": "uuid-v4-doc-id"
}
```

**Example Usage**:

```json
{
  "tool": "knowledge-remove",
  "parameters": {
    "document_id": "uuid-v4-doc-id",
    "confirm": true
  }
}
```

---

### 4. knowledge-show

**Description**: List all documents in the knowledge base with metadata

**Parameters**:

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `limit` | integer | No | Max documents to return | Default: 100, max: 1000 |
| `offset` | integer | No | Pagination offset | Default: 0 |
| `sort_by` | string | No | Sort field (date_added, filename, size) | Valid field name |
| `sort_order` | string | No | Sort order (asc, desc) | Default: desc |

**Response**:

```json
{
  "success": true,
  "documents": [
    {
      "id": "uuid-v4-doc-id-1",
      "filename": "api-documentation.pdf",
      "format": "pdf",
      "size_bytes": 2048576,
      "date_added": "2025-10-26T10:00:00Z",
      "chunk_count": 45,
      "processing_status": "completed",
      "processing_method": "text_extraction"
    },
    {
      "id": "uuid-v4-doc-id-2",
      "filename": "diagram.png",
      "format": "png",
      "size_bytes": 512000,
      "date_added": "2025-10-25T15:30:00Z",
      "chunk_count": 1,
      "processing_status": "completed",
      "processing_method": "image_analysis"
    }
  ],
  "total_count": 2,
  "limit": 100,
  "offset": 0
}
```

**Empty Knowledge Base**:

```json
{
  "success": true,
  "documents": [],
  "total_count": 0,
  "message": "Knowledge base is empty"
}
```

**Example Usage**:

```json
{
  "tool": "knowledge-show",
  "parameters": {
    "limit": 50,
    "offset": 0,
    "sort_by": "date_added",
    "sort_order": "desc"
  }
}
```

---

### 5. knowledge-clear

**Description**: Remove all documents from the knowledge base

**Parameters**:

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `confirm` | boolean | Yes | Must be true to clear | Must be true |
| `confirmation_phrase` | string | Yes | Must be "DELETE ALL" | Exact match required |

**Response**:

```json
{
  "success": true,
  "documents_removed": 42,
  "embeddings_removed": 1850,
  "storage_freed_mb": 125.5,
  "message": "Knowledge base cleared successfully"
}
```

**Confirmation Error**:

```json
{
  "success": false,
  "error": "confirmation_required",
  "message": "This action will delete ALL documents. Set confirm=true and confirmation_phrase='DELETE ALL' to proceed",
  "current_document_count": 42
}
```

**Example Usage**:

```json
{
  "tool": "knowledge-clear",
  "parameters": {
    "confirm": true,
    "confirmation_phrase": "DELETE ALL"
  }
}
```

---

### 6. knowledge-status

**Description**: Get knowledge base statistics and health status

**Parameters**: None

**Response**:

```json
{
  "success": true,
  "knowledge_base": {
    "name": "default",
    "document_count": 42,
    "total_chunks": 1850,
    "total_size_bytes": 131072000,
    "total_size_mb": 125.0,
    "average_chunks_per_document": 44.0,
    "storage_path": "/data/documents",
    "vector_db_path": "/data/chromadb"
  },
  "health": {
    "status": "healthy",
    "vector_db_connected": true,
    "storage_accessible": true,
    "embedding_model_loaded": true
  },
  "configuration": {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "chunk_size": 500,
    "max_file_size_mb": 100
  },
  "last_updated": "2025-10-26T14:30:00Z"
}
```

**Unhealthy Status**:

```json
{
  "success": true,
  "knowledge_base": {...},
  "health": {
    "status": "degraded",
    "vector_db_connected": true,
    "storage_accessible": false,
    "embedding_model_loaded": true,
    "issues": [
      "Storage directory not accessible: Permission denied"
    ]
  }
}
```

**Example Usage**:

```json
{
  "tool": "knowledge-status",
  "parameters": {}
}
```

---

### 7. knowledge-task-status

**Description**: Get status of an async processing task

**Parameters**:

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `task_id` | string | Yes | Task ID returned from async operation | Valid UUID |

**Response (In Progress)**:

```json
{
  "success": true,
  "task_id": "uuid-v4-task-id",
  "status": "running",
  "progress": 0.65,
  "current_step": "Generating embeddings",
  "completed_steps": 13,
  "total_steps": 20,
  "elapsed_time_seconds": 15.5,
  "estimated_remaining_seconds": 8.2
}
```

**Response (Completed)**:

```json
{
  "success": true,
  "task_id": "uuid-v4-task-id",
  "status": "completed",
  "progress": 1.0,
  "result": {
    "document_id": "uuid-v4-doc-id",
    "filename": "example.pdf",
    "chunks_created": 45
  },
  "total_time_seconds": 23.7
}
```

**Response (Failed)**:

```json
{
  "success": false,
  "task_id": "uuid-v4-task-id",
  "status": "failed",
  "error": "ocr_failed",
  "message": "OCR processing failed: Tesseract not found",
  "elapsed_time_seconds": 5.2
}
```

**Example Usage**:

```json
{
  "tool": "knowledge-task-status",
  "parameters": {
    "task_id": "uuid-v4-task-id"
  }
}
```

---

## MCP Protocol Details

### Tool Registration

Tools are registered with the MCP server using JSON Schema for parameter validation:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("knowledge-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="knowledge-add",
            description="Add a document or image to the knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "metadata": {"type": "object"},
                    "force_ocr": {"type": "boolean"},
                    "async": {"type": "boolean"}
                },
                "required": ["file_path"]
            }
        ),
        # ... other tools
    ]
```

### Error Handling

All errors follow MCP error response format:

```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "error": {
    "code": -32000,
    "message": "Error description",
    "data": {
      "error_type": "validation_error",
      "details": {...}
    }
  }
}
```

**Error Codes**:
- `-32700`: Parse error (invalid JSON)
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32000` to `-32099`: Server-defined errors

### Progress Notifications

For long-running operations, progress notifications are sent via MCP progress notification:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/progress",
  "params": {
    "progressToken": "task-uuid",
    "progress": 0.5,
    "total": 1.0,
    "message": "Processing page 5 of 10"
  }
}
```

### Cancellation

Clients can cancel long-running operations:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/cancel",
  "params": {
    "taskId": "task-uuid"
  }
}
```

## Transport

### HTTP Streaming Transport

**Endpoint**: `http://localhost:3000/mcp`

**Method**: POST (for requests), SSE (for streaming responses)

**Request Format**:
```http
POST /mcp HTTP/1.1
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "knowledge-search",
    "arguments": {
      "query": "authentication",
      "top_k": 5
    }
  }
}
```

**Response Format**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{...json response...}"
      }
    ]
  }
}
```

### WebSocket Alternative

For real-time bidirectional communication:

**Endpoint**: `ws://localhost:3000/mcp`

Messages use same JSON-RPC 2.0 format as HTTP.

## Testing Contracts

### Contract Tests

Each tool must have contract tests verifying:
1. Parameter validation (required, types, ranges)
2. Response schema compliance
3. Error handling (all error cases)
4. Progress notifications (for async operations)

### Example Contract Test

```python
def test_knowledge_add_contract():
    # Valid request
    response = call_tool("knowledge-add", {
        "file_path": "/test/doc.pdf",
        "async": True
    })
    assert response["success"] is True
    assert "task_id" in response
    
    # Invalid request - missing required param
    response = call_tool("knowledge-add", {})
    assert response["success"] is False
    assert response["error"] == "missing_required_parameter"
    
    # Invalid file format
    response = call_tool("knowledge-add", {
        "file_path": "/test/doc.xyz"
    })
    assert response["error"] == "unsupported_format"
```

## Compatibility

### MCP Client Compatibility

Tested and compatible with:
- ✅ Claude Desktop
- ✅ GitHub Copilot (via MCP adapter)
- ✅ Amazon Q CLI
- ✅ Any MCP 2025-06-18 compliant client

### Version Negotiation

Server advertises supported MCP version in capabilities:

```json
{
  "protocolVersion": "2025-06-18",
  "capabilities": {
    "tools": {
      "listChanged": true
    },
    "prompts": {
      "listChanged": false
    }
  },
  "serverInfo": {
    "name": "knowledge-server",
    "version": "1.0.0"
  }
}
```
