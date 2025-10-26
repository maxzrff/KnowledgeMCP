# MCP Knowledge Server

A Model Context Protocol (MCP) server that enables AI coding assistants and agentic tools to leverage local knowledge through semantic search.

**Status**: ✅ **Fully Operational** - All user stories implemented and verified

## Features

- ✅ **Semantic Search**: Natural language queries over your document collection
- ✅ **Multi-Format Support**: PDF, DOCX, PPTX, XLSX, HTML, and images (JPG, PNG, SVG)
- ✅ **Intelligent OCR**: Automatic decision between text extraction and OCR
- ✅ **Async Processing**: Background indexing with progress tracking
- ✅ **MCP Integration**: Compatible with Claude Desktop, GitHub Copilot, and other MCP clients
- ✅ **Local & Private**: All processing happens locally, no data leaves your system

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
    
    # Add document
    doc_id = await service.add_document(
        Path("document.pdf"),
        metadata={"category": "technical"},
        async_processing=False
    )
    
    # Search
    results = await service.search("neural networks", top_k=5)
    for result in results:
        print(f"{result['filename']}: {result['relevance_score']:.2f}")
        print(f"  {result['chunk_text'][:100]}...")
    
    # Get statistics
    stats = service.get_statistics()
    print(f"\nDocuments: {stats['document_count']}")
    print(f"Chunks: {stats['total_chunks']}")

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

The server exposes 7 MCP tools for AI assistants:

1. **knowledge-add**: Add documents to knowledge base
2. **knowledge-search**: Semantic search with natural language queries
3. **knowledge-show**: List all documents
4. **knowledge-remove**: Remove specific documents
5. **knowledge-clear**: Clear entire knowledge base
6. **knowledge-status**: Get statistics and health status
7. **knowledge-task-status**: Check async processing task status

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

### GitHub Copilot

Configure MCP adapter in your Copilot settings with server URL: `http://localhost:3000`

## Architecture

- **Vector Database**: ChromaDB for semantic search
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions, fast inference)
- **OCR Engine**: Tesseract for scanned documents
- **Protocol**: MCP over stdio for AI assistant integration

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

- [Implementation Progress](IMPLEMENTATION_PROGRESS.md) - Detailed progress report
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

✅ **US2**: Search Knowledge Semantically  
- Natural language queries
- Relevance-ranked results
- Fast semantic search

✅ **US3**: Manage Knowledge Base  
- List all documents
- Remove specific documents
- Clear knowledge base
- View statistics

✅ **US4**: Integrate with AI Tools via MCP  
- 7 MCP tools implemented
- JSON-RPC compatible
- Ready for AI assistant integration

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
