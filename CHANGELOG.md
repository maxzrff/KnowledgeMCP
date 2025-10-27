# Changelog

All notable changes to the MCP Knowledge Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-10-27

### Added
- **Multi-Context Support**
  - Organize documents into separate contexts for better organization
  - 4 new MCP tools: `knowledge-context-create`, `knowledge-context-list`, `knowledge-context-show`, `knowledge-context-delete`
  - Context-scoped search for faster, more relevant results
  - Documents can belong to multiple contexts simultaneously
  - Each context uses a separate ChromaDB collection for isolation
  - Default context ensures backward compatibility
  - Updated `knowledge-add`, `knowledge-search`, `knowledge-show` tools with context parameter
  - Multiple files can be added to the same context
- Smart OCR Implementation (v0.2.0)
  - Automatic detection of scan-only PDFs
  - OCR applied only when text extraction fails or produces poor results
  - Force OCR mode for always applying OCR
  - Processing method tracking (text_extraction, ocr, image_analysis)
  - OCR confidence scores in document metadata
- HTTP transport support via FastMCP for GitHub Copilot CLI integration (v0.1.1)
- Streamable HTTP endpoint at `http://localhost:3000`
- Server management script (`server.sh`) for start/stop/status/logs operations
- Comprehensive configuration documentation in `docs/CONFIGURATION.md`
- Server management guide in `docs/SERVER_MANAGEMENT.md`
- MIT License

### Fixed
- **Critical**: Document removal now persists across server restarts
  - Root cause: `remove_document()` relied on cached `embedding_ids` that weren't available after server restart
  - Solution: Query ChromaDB directly by `document_id` filter to find and delete all embeddings
  - Impact: Removed documents no longer reappear after server restart
- Context-related tools now properly available when server runs in HTTP mode

### Changed
- Server now automatically detects transport mode (HTTP vs stdio)
- Improved logging for document removal operations
- Updated README with GitHub Copilot CLI configuration examples
- Updated README with multi-context organization examples
- Tool count increased from 7 to 11 (7 document + 4 context tools)
- Enhanced documentation with multi-context usage examples

## [0.1.0] - 2025-10-26

### Added
- Initial release of MCP Knowledge Server
- Semantic search over local documents using ChromaDB
- Multi-format document support: PDF, DOCX, PPTX, XLSX, HTML, Images (JPG, PNG, SVG)
- Intelligent OCR with automatic text extraction vs OCR decision
- Async document processing with progress tracking
- 7 MCP tools: add, search, show, remove, clear, status, task-status
- MCP integration for Claude Desktop (stdio transport)
- Local and private processing - no data leaves your system
- Configurable via YAML files and environment variables
- Comprehensive test suite with unit, integration, and e2e tests
- Quick start script for automated setup

### Technical Details
- Python 3.11+ support
- ChromaDB for vector storage
- sentence-transformers/all-MiniLM-L6-v2 for embeddings (384 dimensions)
- Tesseract OCR integration for scanned documents
- Pydantic for configuration validation
- FastMCP for HTTP endpoint management

### Documentation
- Complete README with quick start guide
- Implementation progress report
- Feature specification and implementation plan
- MCP tool API contracts
- Server management documentation
- Configuration guide

## Release Notes

### For GitHub Copilot CLI Users

To use with Copilot CLI, add to `~/.copilot/mcp-config.json`:

```json
{
  "knowledge": {
    "type": "http",
    "url": "http://localhost:3000"
  }
}
```

Then start the server with:
```bash
./server.sh start
```

### For Claude Desktop Users

Claude Desktop uses stdio transport. Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "knowledge": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "/path/to/KnowledgeMCP"
    }
  }
}
```

### Breaking Changes

None yet - this is the initial release.

### Known Issues

None at this time.

### Migration Guide

Not applicable - initial release.

---

## Version Scheme

- Major version: Breaking changes to MCP API or configuration
- Minor version: New features, non-breaking changes
- Patch version: Bug fixes, documentation updates
