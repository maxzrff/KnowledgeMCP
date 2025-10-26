# Quickstart Guide: MCP Knowledge Server

**Date**: 2025-10-26  
**Feature**: MCP Knowledge Server  
**Audience**: Developers integrating the knowledge server

## Overview

This quickstart guide walks through setting up the MCP Knowledge Server, adding documents, performing searches, and integrating with AI coding assistants.

## Prerequisites

- Python 3.11 or higher
- 2GB+ available memory
- 500MB+ disk space for vector database
- Tesseract OCR (for scanned document support)

### Installing Tesseract OCR

**Ubuntu/Debian**:
```bash
sudo apt-get install tesseract-ocr
```

**macOS**:
```bash
brew install tesseract
```

**Windows**:
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/KnowledgeMCP.git
cd KnowledgeMCP
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages will include:
- chromadb
- sentence-transformers
- mcp
- PyPDF2
- pdfplumber
- python-docx
- python-pptx
- openpyxl
- beautifulsoup4
- Pillow
- pytesseract
- fastapi
- uvicorn
- pydantic
- pytest

### 4. Download Embedding Model

First run will automatically download the embedding model (~80MB). To pre-cache:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

## Configuration

### Default Configuration

Create `config.yaml` in the root directory:

```yaml
storage:
  documents_path: ./data/documents
  vector_db_path: ./data/chromadb
  model_cache_path: ~/.cache/huggingface

embedding:
  model_name: sentence-transformers/all-MiniLM-L6-v2
  batch_size: 32
  device: cpu  # or cuda if GPU available

chunking:
  chunk_size: 500
  chunk_overlap: 50
  strategy: sentence

processing:
  max_concurrent_tasks: 3
  ocr_confidence_threshold: 0.6
  max_file_size_mb: 100

mcp:
  host: 0.0.0.0
  port: 3000
  transport: http
```

### Environment Variable Overrides

Override any config with environment variables:

```bash
export KNOWLEDGE_STORAGE_PATH=/custom/path
export KNOWLEDGE_MCP_PORT=8080
export KNOWLEDGE_MAX_FILE_SIZE_MB=200
```

## Running the Server

### Start MCP Server

```bash
python -m src.mcp.server
```

Expected output:
```
INFO: Knowledge Server starting...
INFO: Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
INFO: Model loaded successfully (cache hit)
INFO: ChromaDB initialized at ./data/chromadb
INFO: MCP server listening on http://0.0.0.0:3000
INFO: Ready to accept connections
```

### Verify Server Health

```bash
curl http://localhost:3000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "mcp_version": "2025-06-18"
}
```

## Basic Usage

### Example 1: Add a PDF Document

**Using Python Client**:

```python
from mcp import Client

client = Client("http://localhost:3000/mcp")

# Add document asynchronously
response = client.call_tool("knowledge-add", {
    "file_path": "/path/to/document.pdf",
    "metadata": {
        "author": "John Doe",
        "category": "technical-docs"
    },
    "async": True
})

print(f"Task ID: {response['task_id']}")
print(f"Estimated time: {response['estimated_time_seconds']}s")

# Check task progress
import time
while True:
    status = client.call_tool("knowledge-task-status", {
        "task_id": response['task_id']
    })
    
    print(f"Progress: {status['progress'] * 100:.1f}% - {status['current_step']}")
    
    if status['status'] == 'completed':
        print(f"Document added: {status['result']['document_id']}")
        print(f"Chunks created: {status['result']['chunks_created']}")
        break
    
    time.sleep(2)
```

**Output**:
```
Task ID: 550e8400-e29b-41d4-a716-446655440000
Estimated time: 30s
Progress: 25.0% - Extracting text from PDF
Progress: 50.0% - Chunking text
Progress: 75.0% - Generating embeddings
Progress: 100.0% - Storing in vector database
Document added: 7c9e6679-7425-40de-944b-e07fc1f90ae7
Chunks created: 45
```

### Example 2: Search Knowledge Base

```python
# Search for relevant information
results = client.call_tool("knowledge-search", {
    "query": "How do I configure authentication?",
    "top_k": 5,
    "min_relevance": 0.5
})

print(f"Found {results['total_results']} results in {results['search_time_ms']}ms\n")

for result in results['results']:
    print(f"📄 {result['filename']} (page {result['metadata']['page_num']})")
    print(f"   Relevance: {result['relevance_score']:.2f}")
    print(f"   {result['chunk_text'][:200]}...")
    print()
```

**Output**:
```
Found 3 results in 125ms

📄 auth-guide.pdf (page 5)
   Relevance: 0.89
   To configure authentication, first set up the OAuth2 provider in your configuration file. Add the following settings to config.yaml: auth: provider: oauth2 client_id: your-client-id...

📄 api-reference.pdf (page 12)
   Relevance: 0.76
   The authentication endpoint accepts Bearer tokens in the Authorization header. Example: Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

📄 quickstart.md (page 1)
   Relevance: 0.65
   Authentication Setup: Before using the API, you need to authenticate. Follow these steps: 1. Obtain API credentials from the dashboard 2. Configure your client...
```

### Example 3: List All Documents

```python
# Get all documents
docs = client.call_tool("knowledge-show", {
    "limit": 100,
    "sort_by": "date_added",
    "sort_order": "desc"
})

print(f"Total documents: {docs['total_count']}\n")

for doc in docs['documents']:
    size_mb = doc['size_bytes'] / (1024 * 1024)
    print(f"📄 {doc['filename']}")
    print(f"   Format: {doc['format'].upper()} | Size: {size_mb:.1f} MB | Chunks: {doc['chunk_count']}")
    print(f"   Added: {doc['date_added']} | Method: {doc['processing_method']}")
    print()
```

**Output**:
```
Total documents: 3

📄 auth-guide.pdf
   Format: PDF | Size: 2.5 MB | Chunks: 45
   Added: 2025-10-26T10:00:00Z | Method: text_extraction

📄 diagram.png
   Format: PNG | Size: 0.5 MB | Chunks: 1
   Added: 2025-10-25T15:30:00Z | Method: image_analysis

📄 scanned-doc.pdf
   Format: PDF | Size: 8.2 MB | Chunks: 123
   Added: 2025-10-24T09:15:00Z | Method: ocr
```

### Example 4: Get Knowledge Base Status

```python
# Check knowledge base statistics
status = client.call_tool("knowledge-status")

kb = status['knowledge_base']
health = status['health']

print(f"📊 Knowledge Base: {kb['name']}")
print(f"   Documents: {kb['document_count']}")
print(f"   Chunks: {kb['total_chunks']}")
print(f"   Total Size: {kb['total_size_mb']:.1f} MB")
print(f"   Avg Chunks/Doc: {kb['average_chunks_per_document']:.1f}")
print()
print(f"🏥 Health: {health['status'].upper()}")
print(f"   Vector DB: {'✅' if health['vector_db_connected'] else '❌'}")
print(f"   Storage: {'✅' if health['storage_accessible'] else '❌'}")
print(f"   Model: {'✅' if health['embedding_model_loaded'] else '❌'}")
```

**Output**:
```
📊 Knowledge Base: default
   Documents: 42
   Chunks: 1,850
   Total Size: 125.0 MB
   Avg Chunks/Doc: 44.0

🏥 Health: HEALTHY
   Vector DB: ✅
   Storage: ✅
   Model: ✅
```

### Example 5: Remove Document

```python
# Remove a specific document
response = client.call_tool("knowledge-remove", {
    "document_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "confirm": True
})

print(f"✅ Removed: {response['filename']}")
print(f"   Chunks removed: {response['chunks_removed']}")
```

## Integrating with AI Assistants

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "knowledge": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "/path/to/KnowledgeMCP",
      "env": {
        "KNOWLEDGE_STORAGE_PATH": "/path/to/data"
      }
    }
  }
}
```

Restart Claude Desktop. The knowledge tools will appear in the tool menu.

### GitHub Copilot

Configure MCP adapter:

```json
{
  "mcp": {
    "servers": [
      {
        "name": "knowledge",
        "url": "http://localhost:3000/mcp"
      }
    ]
  }
}
```

### Amazon Q CLI

```bash
q configure mcp add \
  --name knowledge \
  --url http://localhost:3000/mcp
```

## Common Workflows

### Workflow 1: Building a Project Knowledge Base

```python
import os
from pathlib import Path

# Add all PDFs from docs directory
docs_dir = Path("./project-docs")
for pdf_file in docs_dir.glob("**/*.pdf"):
    print(f"Adding: {pdf_file}")
    client.call_tool("knowledge-add", {
        "file_path": str(pdf_file),
        "async": False  # Wait for completion
    })

print("✅ All documents added!")
```

### Workflow 2: Semantic Code Documentation Search

```python
# AI assistant uses this workflow
def find_implementation_examples(query: str):
    """Find code examples from documentation"""
    results = client.call_tool("knowledge-search", {
        "query": f"code example: {query}",
        "top_k": 3,
        "filters": {
            "format": "pdf",
            "tags": ["code-samples", "api-reference"]
        }
    })
    
    return [r['chunk_text'] for r in results['results']]

# Example: AI asks "How to implement JWT authentication?"
examples = find_implementation_examples("JWT authentication implementation")
for example in examples:
    print(example)
```

### Workflow 3: Monitoring and Maintenance

```python
import schedule
import time

def health_check():
    """Regular health check"""
    status = client.call_tool("knowledge-status")
    
    if status['health']['status'] != 'healthy':
        print("⚠️  WARNING: Knowledge server unhealthy!")
        print(f"   Issues: {status['health'].get('issues', [])}")
        # Send alert...

# Run health check every 5 minutes
schedule.every(5).minutes.do(health_check)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Troubleshooting

### Issue: Model Download Timeout

**Problem**: First run fails with timeout downloading embedding model

**Solution**: Pre-cache the model:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Issue: OCR Not Working

**Problem**: Scanned PDFs fail with "Tesseract not found"

**Solution**: Install Tesseract OCR:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Verify installation
tesseract --version
```

### Issue: Out of Memory

**Problem**: Server crashes with large documents

**Solution**: Reduce concurrent processing:
```yaml
processing:
  max_concurrent_tasks: 1  # Reduce from 3
  max_file_size_mb: 50     # Reduce file size limit
```

### Issue: Slow Search Performance

**Problem**: Searches take >5 seconds

**Solution**: 
1. Check document count: `knowledge-status`
2. If >10,000 documents, consider splitting into multiple knowledge bases
3. Increase `embedding.batch_size` in config
4. Ensure ChromaDB using SSD storage

## Next Steps

1. **Add Your Documents**: Start building your knowledge base
2. **Configure AI Assistant**: Integrate with your preferred AI tool
3. **Explore Advanced Features**: Custom chunking strategies, metadata filtering
4. **Monitor Performance**: Set up health checks and logging
5. **Scale Up**: Add more documents and test search performance

## Testing the Implementation

### Run Unit Tests

```bash
pytest tests/unit/ -v --cov=src
```

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

### Run Contract Tests

```bash
pytest tests/contract/ -v
```

### Expected Test Coverage

- Unit tests: 80%+ coverage for core services
- Integration tests: All user workflows covered
- Contract tests: All MCP tools validated

## Performance Benchmarks

Expected performance on standard hardware (4-core CPU, 8GB RAM):

| Operation | Target | Notes |
|-----------|--------|-------|
| Add PDF (10 pages) | <30s | Text extraction mode |
| Add PDF (10 pages, scanned) | <120s | OCR mode |
| Search (100 docs) | <500ms | p95 |
| Search (1000 docs) | <2s | p95 |
| MCP tool call overhead | <100ms | Excluding processing |
| Indexing throughput | 50-100 chunks/sec | Async processing |

## Support

- Documentation: `docs/`
- Issues: GitHub Issues
- API Reference: `contracts/mcp-tools.md`
- Architecture: `docs/architecture.md`
