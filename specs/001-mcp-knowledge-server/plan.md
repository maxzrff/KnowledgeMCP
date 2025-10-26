# Implementation Plan: MCP Knowledge Server

**Branch**: `001-mcp-knowledge-server` | **Date**: 2025-10-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-mcp-knowledge-server/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an MCP server that enables AI coding assistants and agentic tools to leverage local knowledge through semantic search. The server will use ChromaDB for vector storage, all-MiniLM-L6-v2 for embeddings, support multiple document formats (PDF, DOCX, PPTX, XLSX, HTML) and images (JPG, PNG, SVG), implement intelligent OCR/text extraction decision-making, and expose functionality via MCP protocol over HTTP streaming transport. Key features include async background indexing with progress tracking, configurable storage paths and chunking strategies, and compatibility with any MCP client.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: 
- ChromaDB (vector database)
- sentence-transformers (all-MiniLM-L6-v2 embedding model)
- mcp (Model Context Protocol SDK)
- PyPDF2/pdfplumber (PDF processing)
- python-docx (DOCX processing)
- python-pptx (PPTX processing)
- openpyxl (XLSX processing)
- beautifulsoup4 (HTML processing)
- Pillow (image processing)
- pytesseract (OCR engine)
- FastAPI or aiohttp (HTTP server for streaming transport)

**Storage**: ChromaDB vector database (persistent local storage) + filesystem for original documents  
**Testing**: pytest with pytest-asyncio for async operations, pytest-cov for coverage tracking  
**Target Platform**: Cross-platform server (Linux, macOS, Windows) - runs as background service  
**Project Type**: Single project (MCP server application)  
**Performance Goals**: 
- 50-100 chunks/sec indexing throughput
- <2s search response for 1000+ documents
- <500ms MCP tool call response (p95)
- Support 10+ concurrent MCP connections

**Constraints**: 
- <2GB memory for 10,000 documents
- MCP 2025-06-18 specification compliance
- Local cache for embedding model (avoid download timeouts)
- Async processing for non-blocking operations

**Scale/Scope**: 
- Support 10,000+ documents per knowledge base
- Handle documents up to 1000 pages
- Multiple concurrent MCP client connections
- Configurable chunking (500-1000 tokens per chunk)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- **Code Quality Standards**: ✅ PASS
  - Linting: black (formatter), ruff (linter), mypy (type checker)
  - Documentation: Docstrings for all public APIs, architecture decisions in docs/
  - Code structure follows single responsibility and DRY principles
  
- **Testing Standards**: ✅ PASS
  - Target 80% coverage for core knowledge operations (add, search, embedding)
  - Target 70% overall coverage
  - Unit tests for all document processors, embedding logic, MCP tools
  - Integration tests for end-to-end workflows (add→search, MCP protocol)
  - Contract tests for MCP tool interfaces
  
- **User Experience Consistency**: ✅ PASS (MCP Server - CLI/API Interface)
  - Error messages: Clear, actionable (e.g., "Unsupported format: .xyz. Use PDF, DOCX...")
  - Progress indicators: Async processing with progress tracking for long operations
  - Confirmation prompts: Required for destructive operations (clear, remove)
  - Graceful degradation: Partial OCR failures don't block entire document
  
- **Performance Requirements**: ✅ PASS
  - MCP tool response: <500ms p95 (excluding document processing)
  - Search queries: <2s for 1000+ documents
  - Indexing throughput: 50-100 chunks/sec
  - Memory: <2GB for 10,000 documents
  - Monitoring: Logging for performance metrics and errors

**Quality Gates**: All constitution gates addressed in this plan.

*No deviations from constitution principles - see Complexity Tracking section.*

## Project Structure

### Documentation (this feature)

```text
specs/001-mcp-knowledge-server/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── mcp-tools.md     # MCP tool definitions
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── document.py          # Document entity with metadata
│   ├── embedding.py         # Embedding entity
│   ├── search_result.py     # SearchResult entity
│   └── knowledge_base.py    # KnowledgeBase aggregate
├── services/
│   ├── document_processor.py     # Document processing orchestration
│   ├── text_extractor.py         # Text extraction from documents
│   ├── ocr_service.py            # OCR processing
│   ├── embedding_service.py      # Embedding generation with caching
│   ├── vector_store.py           # ChromaDB wrapper
│   ├── knowledge_service.py      # Core knowledge operations
│   └── processing_strategy.py    # OCR vs text extraction decision
├── processors/
│   ├── base.py              # Base document processor interface
│   ├── pdf_processor.py     # PDF processing
│   ├── docx_processor.py    # DOCX processing
│   ├── pptx_processor.py    # PPTX processing
│   ├── xlsx_processor.py    # XLSX processing
│   ├── html_processor.py    # HTML processing
│   └── image_processor.py   # Image processing
├── mcp/
│   ├── server.py            # MCP server implementation
│   ├── tools.py             # MCP tool definitions
│   └── transport.py         # HTTP streaming transport
├── config/
│   ├── settings.py          # Configuration management
│   └── default_config.yaml  # Default configuration
└── utils/
    ├── chunking.py          # Text chunking utilities
    ├── validation.py        # File format validation
    └── logging_config.py    # Logging setup

tests/
├── unit/
│   ├── test_processors/
│   ├── test_services/
│   ├── test_models/
│   └── test_utils/
├── integration/
│   ├── test_knowledge_workflows.py
│   ├── test_mcp_protocol.py
│   └── test_async_processing.py
└── contract/
    └── test_mcp_tools.py

docs/
├── architecture.md          # System architecture
├── configuration.md         # Configuration guide
└── mcp-integration.md       # MCP client integration guide
```

**Structure Decision**: Single project structure selected. This is a standalone MCP server application with no frontend/backend split. All components are co-located in `src/` with clear separation of concerns: models (entities), services (business logic), processors (document-specific logic), mcp (protocol layer), and utils (shared utilities). Tests mirror source structure with unit/integration/contract separation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. All principles are satisfied by the proposed architecture.
