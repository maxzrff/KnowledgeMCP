[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/maxzrff-knowledgemcp-badge.png)](https://mseep.ai/app/maxzrff-knowledgemcp)

# MCP Knowledge Server

A Model Context Protocol (MCP) server that enables AI coding assistants and agentic tools to leverage local knowledge through semantic search.

**Status**: ✅ **Fully Operational** - All user stories implemented and verified

## Features

- ✅ **Semantic Search**: Natural language queries over your document collection
- ✅ **Multi-Context Support**: Organize documents into separate contexts for focused search
- ✅ **Multi-Format Support**: PDF, DOCX, PPTX, XLSX, HTML, and images (JPG, PNG, SVG)
- ✅ **Smart OCR**: Automatically detects scan-only PDFs and applies OCR when needed
- ✅ **Async Processing**: Background indexing with progress tracking
- ✅ **Persistent Storage**: ChromaDB vector store with reliable document removal
- ✅ **HTTP & Stdio Transports**: Compatible with GitHub Copilot CLI and Claude Desktop
- ✅ **MCP Integration**: Compatible with Claude Desktop, GitHub Copilot, and other MCP clients
- ✅ **Local & Private**: All processing happens locally, no data leaves your system

## Multi-Context Organization

Organize your documents into separate contexts for better organization and focused search results.

### What are Contexts?

Contexts are isolated knowledge domains that let you:
- **Organize by Topic**: Separate AWS docs from healthcare docs from project-specific docs
- **Search Efficiently**: Search within a specific context for faster, more relevant results
- **Multi-Domain Documents**: Add the same document to multiple contexts
- **Flexible Organization**: Each context is a separate ChromaDB collection

### Creating and Using Contexts

```python
from src.services.context_service import ContextService

# Create contexts
context_service = ContextService()
await context_service.create_context("aws-architecture", "AWS WAFR and architecture docs")
await context_service.create_context("healthcare", "Medical and compliance documents")

# Add documents to specific contexts
doc_id = await service.add_document(
    Path("wafr.pdf"),
    contexts=["aws-architecture"]
)

# Add to multiple contexts
doc_id = await service.add_document(
    Path("fin-services-lens.pdf"),
    contexts=["aws-architecture", "healthcare"]
)

# Search within a context
results = await service.search("security pillar", context="aws-architecture")

# Search across all contexts
results = await service.search("best practices")  # No context = search all
```

### MCP Context Tools

```bash
# Create context
knowledge-context-create aws-docs --description "AWS documentation"

# List all contexts
knowledge-context-list

# Show context details
knowledge-context-show aws-docs

# Add document to context
knowledge-add /path/to/doc.pdf --contexts aws-docs

# Add to multiple contexts
knowledge-add /path/to/doc.pdf --contexts aws-docs,healthcare

# Search in specific context
knowledge-search "security" --context aws-docs

# Delete context
knowledge-context-delete test-context --confirm true
```

### Default Context

All documents without a specified context go to the "default" context automatically. This ensures backward compatibility with existing workflows.

## Smart OCR Processing

The server includes intelligent OCR capabilities that automatically detect when OCR is needed:

### Automatic OCR Detection

The system analyzes extracted text quality and automatically applies OCR when:
- Extracted text is less than 100 characters (likely a scan)
- Text has less than 70% alphanumeric characters (gibberish/encoding issues)

### Force OCR Mode

You can force OCR processing even when text extraction is available:

```python
# Python API
doc_id = await service.add_document(
    Path("document.pdf"),
    force_ocr=True  # Force OCR regardless of text quality
)

# MCP Tool (via GitHub Copilot or Claude)
knowledge-add /path/to/document.pdf --force_ocr=true
```

### OCR Requirements

For OCR functionality, install Tesseract OCR:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler

# Windows (via Chocolatey)
choco install tesseract poppler
```

### OCR Configuration

Configure OCR behavior in `config.yaml`:

```yaml
ocr:
  enabled: true              # Enable/disable OCR
  language: eng              # OCR language (eng, fra, deu, spa, etc.)
  force_ocr: false           # Global force OCR setting
  confidence_threshold: 0.0  # Accept all OCR results
```

### Processing Method Tracking

All documents include metadata showing how they were processed:
- `text_extraction`: Standard text extraction
- `ocr`: OCR processing was used
- `image_analysis`: Image-only documents

Check processing method in document metadata:

```python
documents = service.list_documents()
for doc in documents:
    print(f"{doc.filename}: {doc.processing_method}")
    if doc.metadata.get("ocr_used"):
        confidence = doc.metadata.get("ocr_confidence", 0)
        print(f"  OCR confidence: {confidence:.2f}")
```

## Quick Start

### Prerequisites

- Python 3.11+ or Python 3.12
- Tesseract OCR (optional, for scanned documents)

### Automated Setup

```bash
# One-command setup and demo
./quickstart.sh
```

This will:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Download embedding model
- ✅ Run end-to-end demo
- ✅ Show next steps

### Manual Installation

```bash
# Clone repository
git clone https://github.com/yourusername/KnowledgeMCP.git
cd KnowledgeMCP

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download embedding model (first run, ~91MB)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Basic Usage

```python
from pathlib import Path
from src.services.knowledge_service import KnowledgeService
import asyncio

async def main():
    # Initialize service
    service = KnowledgeService()
    
    # Add document to specific context
    doc_id = await service.add_document(
        Path("document.pdf"),
        metadata={"category": "technical"},
        contexts=["aws-docs"],  # Optional: organize by context
        async_processing=False
    )
    
    # Search within a context (faster, more focused)
    results = await service.search("neural networks", context="aws-docs", top_k=5)
    for result in results:
        print(f"{result['filename']}: {result['relevance_score']:.2f}")
        print(f"  Context: {result.get('context', 'default')}")
        print(f"  {result['chunk_text'][:100]}...")
    
    # Search across all contexts
    all_results = await service.search("neural networks", top_k=5)
    
    # Get statistics
    stats = service.get_statistics()
    print(f"\nDocuments: {stats['document_count']}")
    print(f"Chunks: {stats['total_chunks']}")
    print(f"Contexts: {stats['context_count']}")

asyncio.run(main())
```

### Running the MCP Server

```bash
# Using the management script (recommended)
./server.sh start       # Start server in background
./server.sh status      # Check if running
./server.sh logs        # View live logs
./server.sh stop        # Stop server
./server.sh restart     # Restart server

# Or run directly (foreground)
python -m src.mcp.server
```

The server script provides:
- ✅ Background process management
- ✅ PID file tracking
- ✅ Log file management
- ✅ Status checking
- ✅ Graceful shutdown

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end demo
python tests/e2e_demo.py
```

## MCP Tools Available

The server exposes 11 MCP tools for AI assistants:

### Document Management
1. **knowledge-add**: Add documents to knowledge base (with optional context assignment)
2. **knowledge-search**: Semantic search with natural language queries (context-aware)
3. **knowledge-show**: List all documents (filterable by context)
4. **knowledge-remove**: Remove specific documents
5. **knowledge-clear**: Clear entire knowledge base
6. **knowledge-status**: Get statistics and health status
7. **knowledge-task-status**: Check async processing task status

### Context Management
8. **knowledge-context-create**: Create a new context for organizing documents
9. **knowledge-context-list**: List all contexts with statistics
10. **knowledge-context-show**: Show details of a specific context
11. **knowledge-context-delete**: Delete a context (documents remain in other contexts)

## Configuration

The server is configured via `config.yaml` in the project root. A default configuration is provided.

### Configuration File

```yaml
# config.yaml - Default configuration provided
storage:
  documents_path: ./data/documents
  vector_db_path: ./data/chromadb

embedding:
  model_name: sentence-transformers/all-MiniLM-L6-v2
  batch_size: 32
  device: cpu

chunking:
  chunk_size: 500
  chunk_overlap: 50
  strategy: sentence

processing:
  max_concurrent_tasks: 3
  max_file_size_mb: 100

ocr:
  enabled: true
  language: eng
  force_ocr: false
  confidence_threshold: 0.0  # Accept all OCR results

logging:
  level: INFO
  format: text

search:
  default_top_k: 10
  max_top_k: 50
```

### Custom Configuration

Create a custom configuration file:

```bash
# Copy template
cp config.yaml.template config.yaml.local

# Edit your settings
nano config.yaml.local

# The server will use config.yaml.local if it exists
```

### Environment Variables

Configuration can be overridden with environment variables (prefix with `KNOWLEDGE_`):

```bash
# Override storage path
export KNOWLEDGE_STORAGE__DOCUMENTS_PATH=/custom/path

# Increase batch size for faster processing
export KNOWLEDGE_EMBEDDING__BATCH_SIZE=64

# Enable debug logging
export KNOWLEDGE_LOGGING__LEVEL=DEBUG

# Increase search results
export KNOWLEDGE_SEARCH__DEFAULT_TOP_K=20

# Use GPU if available
export KNOWLEDGE_EMBEDDING__DEVICE=cuda
```

### Configuration Priority

1. Environment variables (highest priority)
2. `config.yaml.local` (if exists)
3. `config.yaml` (default)

### Key Settings

| Setting | Description | Default | Notes |
|---------|-------------|---------|-------|
| `chunk_size` | Characters per chunk | 500 | Larger = more context |
| `batch_size` | Embeddings per batch | 32 | Higher = faster, more RAM |
| `device` | Computation device | cpu | Use 'cuda' for GPU |
| `max_file_size_mb` | Max file size | 100 | Increase for large docs |
| `log_level` | Logging verbosity | INFO | Use DEBUG for development |
| `collection_prefix` | ChromaDB collection prefix | knowledge_ | Used for context collections |
| `default_context` | Default context name | default | Backward compatibility |

## Integration with AI Assistants

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
        "KNOWLEDGE_STORAGE__DOCUMENTS_PATH": "/path/to/docs"
      }
    }
  }
}
```

**Note**: Claude Desktop uses stdio transport. The server automatically detects the transport mode.

### GitHub Copilot CLI

The server exposes an HTTP endpoint for Copilot CLI integration using MCP Streamable HTTP.

**Step 1: Start the server**
```bash
./server.sh start
```

**Step 2: Configure Copilot CLI**

Add to `~/.copilot/mcp-config.json`:

```json
{
  "knowledge": {
    "type": "http",
    "url": "http://localhost:3000"
  }
}
```

**Step 3: Verify integration**

In Copilot CLI, the following tools will be available:
- `knowledge-add` - Add documents to knowledge base
- `knowledge-search` - Search with natural language queries
- `knowledge-show` - List all documents
- `knowledge-remove` - Remove documents
- `knowledge-clear` - Clear knowledge base
- `knowledge-status` - Get statistics
- `knowledge-task-status` - Check processing status

**Example usage in Copilot CLI:**
```bash
# Create organized contexts
> knowledge-context-create aws-docs --description "AWS architecture documents"

# Add documents to specific contexts
> knowledge-add /path/to/wafr.pdf --contexts aws-docs

# Search within a context for focused results
> knowledge-search "security pillar" --context aws-docs

# Ask Copilot to use the knowledge base
> What are the AWS WAFR security best practices?
```

## Architecture

- **Vector Database**: ChromaDB for semantic search with persistent storage
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions, fast inference)
- **OCR Engine**: Tesseract for scanned documents
- **Protocol**: MCP over HTTP (Streamable HTTP) and stdio transports
- **Server Framework**: FastMCP for HTTP endpoint management

## Performance

Verified performance on standard hardware (4-core CPU, 8GB RAM):

- **Indexing**: Documents processed in <1s (HTML), up to 30s (large PDFs)
- **Search**: <200ms for knowledge bases with dozens of documents
- **Memory**: <500MB baseline, scales with document count
- **Embeddings**: Batch processing, model cached locally

## Project Structure

```
KnowledgeMCP/
├── src/                    # Source code
│   ├── models/            # Data models (Document, Embedding, etc.)
│   ├── services/          # Core services (KnowledgeService, VectorStore)
│   ├── processors/        # Document processors (PDF, DOCX, etc.)
│   ├── mcp/              # MCP server and tools
│   ├── config/           # Configuration management
│   └── utils/            # Utilities (chunking, validation, logging)
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e_demo.py       # End-to-end demonstration
├── docs/                  # Documentation
│   └── SERVER_MANAGEMENT.md  # Server management guide
├── server.sh             # Server management script ⭐
├── quickstart.sh         # Quick setup script ⭐
└── README.md             # This file
```

### Key Scripts

- **`server.sh`** - Start/stop/status management
- **`quickstart.sh`** - Automated setup and demo
- **`tests/e2e_demo.py`** - Full system demonstration

## Documentation

- [Changelog](CHANGELOG.md) - Version history and recent changes
- [Implementation Progress](IMPLEMENTATION_PROGRESS.md) - Detailed progress report
- [Configuration Guide](docs/CONFIGURATION.md) - Complete configuration reference
- [Server Management](docs/SERVER_MANAGEMENT.md) - Server lifecycle management
- [Specification](specs/001-mcp-knowledge-server/spec.md) - Feature specification
- [Implementation Plan](specs/001-mcp-knowledge-server/plan.md) - Technical plan
- [Tasks](specs/001-mcp-knowledge-server/tasks.md) - Task breakdown
- [Quickstart Guide](specs/001-mcp-knowledge-server/quickstart.md) - Detailed usage guide
- [MCP Tool Contracts](specs/001-mcp-knowledge-server/contracts/mcp-tools.md) - API specifications

## Development

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Adding New Document Processors

1. Create processor in `src/processors/`
2. Inherit from `BaseProcessor`
3. Implement `extract_text()` and `extract_metadata()`
4. Register in `TextExtractor`

## Verified User Stories

✅ **US1**: Add Knowledge from Documents  
- Multi-format document ingestion
- Intelligent text extraction vs OCR
- Async processing with progress tracking
- Multi-context assignment

✅ **US2**: Search Knowledge Semantically  
- Natural language queries
- Relevance-ranked results
- Fast semantic search
- Context-scoped and cross-context search

✅ **US3**: Manage Knowledge Base  
- List all documents
- Remove specific documents
- Clear knowledge base
- View statistics
- Context filtering

✅ **US4**: Integrate with AI Tools via MCP  
- 11 MCP tools implemented (7 document + 4 context tools)
- JSON-RPC compatible
- Ready for AI assistant integration

✅ **US5**: Multi-Context Organization  
- Create and manage contexts
- Add documents to multiple contexts
- Search within specific contexts
- Context isolation with separate ChromaDB collections

## License

MIT

## Contributing

Contributions welcome! Please read the specification and implementation plan before submitting PRs.

## Support

- **Issues**: GitHub Issues
- **Documentation**: See `docs/` and `specs/` directories
- **Questions**: Check quickstart guide and API contracts

---

**Built with**: Python, ChromaDB, Sentence Transformers, FastAPI, MCP SDK
