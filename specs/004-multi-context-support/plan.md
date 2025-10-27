# Implementation Plan: Multi-Context Support

**Branch**: `004-multi-context-support` | **Date**: 2025-10-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-multi-context-support/spec.md`

## Summary

Implement multi-context support to allow users to organize documents into separate named contexts (e.g., "aws-architecture", "healthcare-compliance") with context-scoped search capabilities. The system will use ChromaDB's collection-per-context strategy for efficient isolation, provide backward compatibility via "default" context, and support adding documents to multiple contexts simultaneously.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: ChromaDB (vector database), Pydantic (data models), FastMCP (HTTP streaming MCP server)  
**Storage**: ChromaDB persistent storage (one collection per context), filesystem for document files  
**Testing**: pytest with async support, integration tests for vector store operations  
**Target Platform**: Linux server (WSL2), exposed via HTTP streaming MCP protocol  
**Project Type**: Single project (MCP server)  
**Performance Goals**: 
- Context-scoped search 20-30% faster than cross-context search
- Context creation <1s, context listing <2s
- Support 100 contexts with thousands of documents each
**Constraints**: 
- Context names must be alphanumeric with dashes/underscores (1-64 chars)
- "default" context is reserved and auto-created
- Backward compatibility required (no breaking API changes)
**Scale/Scope**: 
- Up to 100 contexts per server instance
- Each context can contain thousands of documents
- Existing documents must migrate to "default" context seamlessly

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- **Code Quality Standards**: ✅
  - Linting: Existing ruff configuration will apply to new code
  - Documentation: All new context APIs will be documented in docstrings
  - Naming: Following existing conventions (PascalCase for classes, snake_case for functions)
  - DRY: Context management logic will be centralized in ContextService class

- **Testing Standards**: ✅
  - Test coverage: Target 80% for new context management code
  - Test types: Unit tests for context CRUD, integration tests for ChromaDB collection management, E2E tests for user scenarios
  - Test-first approach: Will write tests for context validation and collection naming before implementation
  - Tests will be isolated (each test creates/deletes its own contexts)

- **User Experience Consistency**: ✅
  - Error handling: Clear validation messages for invalid context names
  - Feedback: Context operations return success confirmations with context details
  - Backward compatibility: Existing knowledge-add/search/show work without changes
  - Optional parameters: All context parameters are optional with sensible defaults

- **Performance Requirements**: ✅
  - Response time targets: Context creation <1s, context listing <2s
  - Performance improvement: Context-scoped search 20-30% faster than cross-context
  - Monitoring: Will log context operation timings
  - Scalability: Collection-per-context strategy scales linearly

**Quality Gates**: All gates will be enforced:
- Automated testing: Full pytest suite must pass
- Code quality: ruff linting must pass
- Documentation: Context API methods documented
- No performance regressions in existing search functionality

*No deviations required - design aligns with constitution.*

## Project Structure

### Documentation (this feature)

```text
specs/004-multi-context-support/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0: ChromaDB multi-collection patterns, migration strategies
├── data-model.md        # Phase 1: Context entity, updated Document entity
├── quickstart.md        # Phase 1: How to create contexts and search
├── contracts/           # Phase 1: MCP tool contracts for context operations
│   ├── knowledge-context-create.json
│   ├── knowledge-context-list.json
│   ├── knowledge-context-show.json
│   ├── knowledge-context-delete.json
│   └── updated-tools.json  # Updated knowledge-add, knowledge-search, knowledge-show
└── tasks.md             # Phase 2: Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── document.py           # UPDATE: Add contexts: List[str] field
│   ├── context.py            # NEW: Context entity model
│   └── ...
├── services/
│   ├── knowledge_service.py  # UPDATE: Add context parameter handling
│   ├── vector_store.py       # UPDATE: Collection-per-context methods
│   ├── context_service.py    # NEW: Context CRUD operations
│   └── ...
├── mcp/
│   ├── tools.py              # UPDATE: Add 4 new context tools, update 3 existing
│   ├── server.py             # No changes needed
│   └── http_server.py        # No changes needed
├── config/
│   ├── settings.py           # UPDATE: Add context configuration
│   └── ...
└── utils/
    ├── migration.py          # NEW: Migration logic for existing documents
    └── ...

tests/
├── unit/
│   ├── test_context_service.py      # NEW: Context CRUD tests
│   ├── test_context_validation.py   # NEW: Name validation tests
│   └── test_knowledge_service.py    # UPDATE: Add context parameter tests
├── integration/
│   ├── test_vector_store_contexts.py  # NEW: Multi-collection tests
│   ├── test_context_search.py         # NEW: Context-scoped vs cross-context
│   └── test_migration.py              # NEW: Migration validation
└── e2e/
    └── test_multi_context_scenarios.py  # NEW: User scenario tests

config.yaml                    # UPDATE: Add context configuration
README.md                      # UPDATE: Document context feature
```

**Structure Decision**: Single project structure maintained. New context functionality integrated into existing service layer with new ContextService. ChromaDB vector_store.py extended to support multiple collections. Migration utility added to upgrade existing data.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations - feature aligns with constitution standards.*

## Implementation Phases

### Phase 0: Research & Discovery

**Goal**: Understand ChromaDB multi-collection capabilities and migration requirements

**Deliverables**: `research.md`

**Key Questions**:
1. ChromaDB collection naming conventions and limits
2. Collection isolation guarantees (data/search separation)
3. Collection creation/deletion performance characteristics
4. Cross-collection search patterns and performance
5. Existing document count and migration strategy validation
6. Metadata schema evolution for context tracking

**Exit Criteria**: 
- ✅ Confirm ChromaDB supports multiple collections in single persistent directory
- ✅ Validate collection naming pattern (e.g., `context_{name}`)
- ✅ Confirm collections are fully isolated for search operations
- ✅ Document migration approach (re-add to "default" collection)

### Phase 1: Design & Contracts

**Goal**: Define data models, API contracts, and migration plan

**Deliverables**: 
- `data-model.md` - Context and updated Document models
- `quickstart.md` - User guide for context operations
- `contracts/*.json` - MCP tool contracts

**Design Artifacts**:

1. **Context Model** (`src/models/context.py`):
```python
class Context(BaseModel):
    name: str  # Alphanumeric + dash/underscore, 1-64 chars
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    document_count: int
    metadata: Dict[str, Any]
```

2. **Updated Document Model** (`src/models/document.py`):
```python
class Document(BaseModel):
    # Existing fields...
    contexts: List[str] = ["default"]  # NEW: List of context names
```

3. **New MCP Tools**:
   - `knowledge-context-create` - Create named context
   - `knowledge-context-list` - List all contexts with stats
   - `knowledge-context-show` - Show context details and documents
   - `knowledge-context-delete` - Delete context (with confirmation)

4. **Updated MCP Tools**:
   - `knowledge-add` - Add `context` parameter (default: "default")
   - `knowledge-search` - Add `context` parameter (default: null = all contexts)
   - `knowledge-show` - Add `context` parameter (default: null = all contexts)

5. **Migration Plan**:
   - On server startup, check for documents without context metadata
   - Auto-create "default" collection if doesn't exist
   - Migrate existing documents to "default" collection
   - Add migration completion marker to prevent re-runs

**Exit Criteria**:
- ✅ All tool contracts defined with input/output schemas
- ✅ Context validation rules documented (name format, reserved words)
- ✅ Migration plan reviewed and validated
- ✅ Quickstart guide written with examples

### Phase 2: Task Breakdown

**Goal**: Create atomic implementation tasks

**Process**: Run `/speckit.tasks` to generate `tasks.md`

**Expected Tasks** (preview):
1. Implement Context model with validation
2. Create ContextService with CRUD operations
3. Update VectorStore to support collection-per-context
4. Update Document model with contexts field
5. Implement migration utility and startup hook
6. Add 4 new MCP tools for context operations
7. Update 3 existing MCP tools with context parameters
8. Write unit tests for ContextService
9. Write integration tests for multi-collection VectorStore
10. Write E2E tests for multi-context scenarios
11. Update config.yaml with context settings
12. Update README.md with context documentation

**Exit Criteria**:
- ✅ `tasks.md` exists with 15-20 atomic tasks
- ✅ Each task has clear acceptance criteria
- ✅ Dependencies between tasks identified

### Phase 3: Implementation

**Goal**: Execute tasks from Phase 2

**Process**: Run `/speckit.implement` to execute tasks

**Order of Operations**:
1. **Foundation** (Tasks 1-5): Models, services, migration
2. **API Layer** (Tasks 6-7): MCP tool updates
3. **Testing** (Tasks 8-10): Comprehensive test coverage
4. **Documentation** (Tasks 11-12): Config and README updates

**Quality Gates** (per task):
- Code passes ruff linting
- Unit tests written and passing
- Integration tests validate ChromaDB behavior
- Manual testing confirms expected behavior

**Exit Criteria**:
- ✅ All tasks completed and checked off
- ✅ Full test suite passing (pytest)
- ✅ Manual testing validates user scenarios
- ✅ Documentation updated

### Phase 4: Validation & Deployment

**Goal**: Validate feature completeness and deploy

**Validation Steps**:
1. **Functional Testing**:
   - Create 3 contexts: "aws", "healthcare", "general"
   - Add documents to each context
   - Search within specific context (verify isolation)
   - Search across all contexts
   - Delete context and verify cleanup
   - Test backward compatibility (no context specified)

2. **Performance Testing**:
   - Measure context-scoped search vs cross-context search
   - Validate 20-30% improvement target
   - Test with 10+ contexts, 100+ documents each

3. **Migration Testing**:
   - Test with fresh install (no existing data)
   - Test with existing documents (verify migration to "default")
   - Test migration idempotency (multiple restarts)

4. **Error Handling**:
   - Invalid context names
   - Delete non-existent context
   - Add to non-existent context
   - Reserved context names ("default" deletion)

**Deployment Steps**:
1. Stop existing server: `./server.sh stop`
2. Run migration: Server startup auto-migrates
3. Start server: `./server.sh start`
4. Validate MCP tools available in Copilot session
5. Test basic context operations

**Exit Criteria**:
- ✅ All functional tests pass
- ✅ Performance targets met
- ✅ Migration validated with test data
- ✅ Error handling comprehensive
- ✅ Server running with new features accessible

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| ChromaDB collection limit | High - Could block feature | Research in Phase 0, ChromaDB supports many collections |
| Migration data loss | Critical | Migration creates new collection, preserves original data |
| Performance degradation | Medium | Benchmark in Phase 4, optimize if needed |
| Context naming conflicts | Low | Strict validation prevents issues |
| Backward compatibility break | High | "default" context ensures existing behavior unchanged |

## Dependencies

**Blocking This Feature**: None

**Blocked By This Feature**: None (standalone feature)

**Related Features**: Future features could build on contexts (e.g., context sharing, context templates)

## Success Metrics

**Functional**:
- ✅ Users can create named contexts
- ✅ Documents can be added to specific contexts
- ✅ Context-scoped search works correctly
- ✅ Cross-context search works correctly
- ✅ Existing functionality (no context specified) unchanged

**Performance**:
- ✅ Context-scoped search 20-30% faster than cross-context
- ✅ Context creation <1s
- ✅ Context listing <2s
- ✅ Support 100 contexts with thousands of documents

**Quality**:
- ✅ Test coverage ≥80% for new code
- ✅ All linting passes
- ✅ No regressions in existing tests
- ✅ Documentation complete and clear

## Notes

- **ChromaDB Strategy**: Collection-per-context provides best isolation and search performance
- **Migration Approach**: One-time automatic migration on server startup, idempotent
- **Naming Convention**: Collections named `context_{name}` to avoid conflicts
- **Reserved Contexts**: "default" is reserved and cannot be deleted
- **Multi-Context Documents**: Full support for adding documents to multiple contexts simultaneously (comma-separated). Document chunks are duplicated across ChromaDB collections for each context to enable independent context-scoped searches
- **Multiple Files Per Context**: Multiple documents can be added to the same context - there's no limit on documents per context (scalability target: thousands of documents per context)

---

**Status**: Plan Complete ✅  
**Next Step**: Run `/speckit.tasks` to generate task breakdown  
**Estimated Effort**: 2-3 days (12-18 implementation tasks)
