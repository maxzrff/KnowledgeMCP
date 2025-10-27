# Implementation Tasks: Multi-Context Support

**Branch**: `004-multi-context-support` | **Date**: 2025-10-27 | **Plan**: [plan.md](./plan.md)

## Task Organization

Tasks are organized by implementation phase and dependencies. Complete tasks in order within each phase.

## Phase 1: Foundation - Data Models

### Task 1.1: Create Context Model
**File**: `src/models/context.py`
**Estimated Time**: 30 minutes

Create the Context entity model with validation.

**Acceptance Criteria**:
- [ ] Context class inherits from BaseModel (Pydantic)
- [ ] Fields: name (str), description (Optional[str]), created_at (datetime), updated_at (datetime), document_count (int), metadata (Dict[str, Any])
- [ ] Name validation: alphanumeric + dash/underscore, 1-64 chars, regex pattern
- [ ] Reserved name validation: "default" cannot be used in create (can exist, cannot delete)
- [ ] Docstrings document all fields and validation rules
- [ ] Unit tests in `tests/unit/test_context_model.py` cover valid/invalid names

**Dependencies**: None

---

### Task 1.2: Update Document Model
**File**: `src/models/document.py`
**Estimated Time**: 15 minutes

Add contexts field to track which contexts a document belongs to.

**Acceptance Criteria**:
- [ ] Add `contexts: List[str] = ["default"]` field to Document model
- [ ] Default value is ["default"] for backward compatibility
- [ ] Validation ensures contexts list is not empty
- [ ] Update existing tests to handle new field
- [ ] Docstring explains multi-context support

**Dependencies**: Task 1.1

---

## Phase 2: Service Layer - Context Management

### Task 2.1: Create ContextService - Basic CRUD
**File**: `src/services/context_service.py`
**Estimated Time**: 1 hour

Implement service for context CRUD operations.

**Acceptance Criteria**:
- [ ] ContextService class with methods: create_context(), list_contexts(), get_context(), delete_context()
- [ ] create_context() validates name, creates Context object, returns Context
- [ ] list_contexts() returns list of all Context objects with document counts
- [ ] get_context(name) returns Context object or raises NotFoundError
- [ ] delete_context(name) validates not "default", returns success confirmation
- [ ] Unit tests in `tests/unit/test_context_service.py` cover all methods
- [ ] Error handling for duplicate context names, invalid names, reserved names

**Dependencies**: Task 1.1, Task 1.2

---

### Task 2.2: Update VectorStore - Collection Management
**File**: `src/services/vector_store.py`
**Estimated Time**: 1.5 hours

Add collection-per-context support to VectorStore.

**Acceptance Criteria**:
- [ ] Method: get_collection(context_name) returns ChromaDB collection
- [ ] Collection naming: `context_{name}` (e.g., "context_default", "context_aws")
- [ ] Method: create_collection(context_name) creates new collection with metadata
- [ ] Method: delete_collection(context_name) deletes collection and all vectors
- [ ] Method: list_collections() returns list of context names (parse from collection names)
- [ ] Update add_document() to accept context parameter, add to correct collection
- [ ] Update search() to accept optional context parameter (None = search all collections)
- [ ] Integration tests in `tests/integration/test_vector_store_contexts.py` verify collection isolation

**Dependencies**: Task 2.1

---

### Task 2.3: Update KnowledgeService - Context Integration
**File**: `src/services/knowledge_service.py`
**Estimated Time**: 1 hour

Integrate context support into existing knowledge operations.

**Acceptance Criteria**:
- [ ] Update add_document() to accept contexts parameter (List[str], default ["default"])
- [ ] When adding document, loop through contexts and add to each collection
- [ ] Update Document object with contexts list before saving
- [ ] Update search() to accept optional context parameter, pass to VectorStore
- [ ] Update list_documents() to accept optional context filter
- [ ] Update get_document() to include contexts in response
- [ ] Unit tests verify multi-context document handling
- [ ] Backward compatibility: calls without context use "default"

**Dependencies**: Task 2.2

---

## Phase 3: Migration & Startup

### Task 3.1: Create Migration Utility
**File**: `src/utils/migration.py`
**Estimated Time**: 1 hour

Implement migration logic for existing documents.

**Acceptance Criteria**:
- [ ] Function: migrate_to_multi_context(vector_store, knowledge_service)
- [ ] Check for migration marker file (e.g., `.migration_004_complete`)
- [ ] If marker exists, skip migration (idempotent)
- [ ] Create "default" collection if doesn't exist
- [ ] Get all documents from old/default storage
- [ ] For each document without contexts field: set contexts=["default"], re-add to "context_default" collection
- [ ] Create migration marker file on success
- [ ] Log migration progress (documents processed)
- [ ] Integration tests in `tests/integration/test_migration.py` verify migration correctness

**Dependencies**: Task 2.3

---

### Task 3.2: Add Migration to Server Startup
**File**: `src/mcp/server.py` or `src/mcp/http_server.py`
**Estimated Time**: 30 minutes

Hook migration into server initialization.

**Acceptance Criteria**:
- [ ] Call migrate_to_multi_context() during server startup (before accepting requests)
- [ ] Log migration start/completion
- [ ] Handle migration errors gracefully (log and exit if critical)
- [ ] Verify "default" context exists after migration
- [ ] Manual test: start server with existing data, verify migration runs once

**Dependencies**: Task 3.1

---

## Phase 4: MCP Tools - New Context Operations

### Task 4.1: Implement knowledge-context-create Tool
**File**: `src/mcp/tools.py`
**Estimated Time**: 30 minutes

Add MCP tool for creating contexts.

**Acceptance Criteria**:
- [ ] Tool name: `knowledge-context-create`
- [ ] Parameters: name (str, required), description (str, optional), metadata (dict, optional)
- [ ] Calls ContextService.create_context()
- [ ] Returns Context object (name, description, created_at, document_count=0)
- [ ] Error handling: invalid name, duplicate context
- [ ] Docstring with usage examples
- [ ] Contract JSON in `specs/004-multi-context-support/contracts/knowledge-context-create.json`

**Dependencies**: Task 2.1

---

### Task 4.2: Implement knowledge-context-list Tool
**File**: `src/mcp/tools.py`
**Estimated Time**: 20 minutes

Add MCP tool for listing contexts.

**Acceptance Criteria**:
- [ ] Tool name: `knowledge-context-list`
- [ ] Parameters: none (or optional filter params)
- [ ] Calls ContextService.list_contexts()
- [ ] Returns list of Context objects with document counts
- [ ] Sorted by name (default context first)
- [ ] Docstring with usage examples
- [ ] Contract JSON in `specs/004-multi-context-support/contracts/knowledge-context-list.json`

**Dependencies**: Task 2.1

---

### Task 4.3: Implement knowledge-context-show Tool
**File**: `src/mcp/tools.py`
**Estimated Time**: 30 minutes

Add MCP tool for showing context details.

**Acceptance Criteria**:
- [ ] Tool name: `knowledge-context-show`
- [ ] Parameters: name (str, required)
- [ ] Calls ContextService.get_context() and KnowledgeService.list_documents(context=name)
- [ ] Returns Context object + list of documents in that context
- [ ] Error handling: context not found
- [ ] Docstring with usage examples
- [ ] Contract JSON in `specs/004-multi-context-support/contracts/knowledge-context-show.json`

**Dependencies**: Task 2.1, Task 2.3

---

### Task 4.4: Implement knowledge-context-delete Tool
**File**: `src/mcp/tools.py`
**Estimated Time**: 30 minutes

Add MCP tool for deleting contexts.

**Acceptance Criteria**:
- [ ] Tool name: `knowledge-context-delete`
- [ ] Parameters: name (str, required), confirm (bool, required, default=false)
- [ ] Requires confirm=true to delete (safety check)
- [ ] Calls ContextService.delete_context() and VectorStore.delete_collection()
- [ ] Error handling: context not found, cannot delete "default"
- [ ] Returns success message with deleted context name
- [ ] Docstring with usage examples and warnings
- [ ] Contract JSON in `specs/004-multi-context-support/contracts/knowledge-context-delete.json`

**Dependencies**: Task 2.1, Task 2.2

---

## Phase 5: MCP Tools - Update Existing Tools

### Task 5.1: Update knowledge-add Tool
**File**: `src/mcp/tools.py`
**Estimated Time**: 30 minutes

Add context support to document addition.

**Acceptance Criteria**:
- [ ] Add parameter: contexts (str, optional, default="default")
- [ ] Parse comma-separated contexts (e.g., "aws,healthcare") into List[str]
- [ ] Validate all contexts exist before adding document
- [ ] Pass contexts to KnowledgeService.add_document()
- [ ] Return confirmation with contexts list
- [ ] Update docstring with context parameter examples
- [ ] Update contract JSON in `specs/004-multi-context-support/contracts/updated-tools.json`
- [ ] Backward compatibility: no context param uses "default"

**Dependencies**: Task 2.3, Task 4.1

---

### Task 5.2: Update knowledge-search Tool
**File**: `src/mcp/tools.py`
**Estimated Time**: 30 minutes

Add context filtering to search.

**Acceptance Criteria**:
- [ ] Add parameter: context (str, optional, default=null)
- [ ] null/missing = search across all contexts
- [ ] Specific context = search only that context
- [ ] Validate context exists if provided
- [ ] Pass context to KnowledgeService.search()
- [ ] Return results with context information
- [ ] Update docstring with context parameter examples
- [ ] Update contract JSON
- [ ] Backward compatibility: no context param searches all

**Dependencies**: Task 2.3

---

### Task 5.3: Update knowledge-show Tool
**File**: `src/mcp/tools.py`
**Estimated Time**: 20 minutes

Add context filtering to document listing.

**Acceptance Criteria**:
- [ ] Add parameter: context (str, optional, default=null)
- [ ] null/missing = show all documents across contexts
- [ ] Specific context = show only documents in that context
- [ ] Pass context to KnowledgeService.list_documents()
- [ ] Include contexts field in document output
- [ ] Update docstring with context parameter examples
- [ ] Update contract JSON
- [ ] Backward compatibility: no context param shows all

**Dependencies**: Task 2.3

---

## Phase 6: Testing

### Task 6.1: Unit Tests - Context Validation
**File**: `tests/unit/test_context_validation.py`
**Estimated Time**: 45 minutes

Comprehensive tests for context name validation.

**Acceptance Criteria**:
- [ ] Test valid names: "aws", "healthcare-2023", "project_x"
- [ ] Test invalid names: empty, too long (>64 chars), special chars, spaces
- [ ] Test reserved names: cannot create/delete "default"
- [ ] Test case sensitivity (if applicable)
- [ ] All tests pass with pytest

**Dependencies**: Task 1.1

---

### Task 6.2: Integration Tests - Multi-Collection VectorStore
**File**: `tests/integration/test_vector_store_contexts.py`
**Estimated Time**: 1 hour

Test ChromaDB collection isolation and operations.

**Acceptance Criteria**:
- [ ] Test: create multiple collections (3 contexts)
- [ ] Test: add documents to different collections
- [ ] Test: search in specific collection (verify isolation)
- [ ] Test: search across all collections
- [ ] Test: delete collection removes all vectors
- [ ] Test: list collections returns correct context names
- [ ] Performance test: context-scoped search faster than cross-context (20-30%)
- [ ] All tests pass with pytest

**Dependencies**: Task 2.2

---

### Task 6.3: Integration Tests - Context-Scoped Search
**File**: `tests/integration/test_context_search.py`
**Estimated Time**: 1 hour

Validate search behavior across contexts.

**Acceptance Criteria**:
- [ ] Setup: create 3 contexts, add 5 documents to each (different content)
- [ ] Test: search in specific context returns only that context's documents
- [ ] Test: search across all contexts returns documents from all contexts
- [ ] Test: search results include context metadata
- [ ] Test: relevance scores consistent between scoped and cross-context
- [ ] All tests pass with pytest

**Dependencies**: Task 5.2

---

### Task 6.4: E2E Tests - Multi-Context Scenarios
**File**: `tests/e2e/test_multi_context_scenarios.py`
**Estimated Time**: 1.5 hours

Test complete user workflows.

**Acceptance Criteria**:
- [ ] Scenario 1: Create context, add documents, search within context, delete context
- [ ] Scenario 2: Add document to multiple contexts simultaneously, verify in both
- [ ] Scenario 3: Backward compatibility - no context specified, uses default
- [ ] Scenario 4: List all contexts, show specific context details
- [ ] Scenario 5: Error handling - invalid context names, delete non-existent context
- [ ] All scenarios pass end-to-end
- [ ] All tests pass with pytest

**Dependencies**: All Phase 4 and Phase 5 tasks

---

## Phase 7: Configuration & Documentation

### Task 7.1: Update Configuration
**File**: `config.yaml`
**Estimated Time**: 15 minutes

Add context-related configuration options.

**Acceptance Criteria**:
- [ ] Add section: `contexts:`
- [ ] Config: `default_context: "default"` (for backward compatibility)
- [ ] Config: `max_contexts: 100` (scalability limit)
- [ ] Config: `context_name_pattern: "^[a-zA-Z0-9_-]{1,64}$"` (validation regex)
- [ ] Comments explain each setting
- [ ] Validate config loads correctly on server startup

**Dependencies**: None (can be done anytime)

---

### Task 7.2: Update README - Context Feature
**File**: `README.md`
**Estimated Time**: 30 minutes

Document multi-context support for users.

**Acceptance Criteria**:
- [ ] Add section: "Multi-Context Support"
- [ ] Explain what contexts are and why use them
- [ ] Document all 4 new MCP tools with examples
- [ ] Document updated tools (knowledge-add, knowledge-search, knowledge-show) with context examples
- [ ] Add examples: create context, add to multiple contexts, search specific context
- [ ] Add migration notes (existing documents in "default")
- [ ] Add best practices (naming conventions, context organization)

**Dependencies**: All implementation tasks complete

---

### Task 7.3: Create Quickstart Guide
**File**: `specs/004-multi-context-support/quickstart.md`
**Estimated Time**: 30 minutes

User-friendly guide for getting started with contexts.

**Acceptance Criteria**:
- [ ] Section: Quick Start (5-minute tutorial)
- [ ] Step 1: Create your first context
- [ ] Step 2: Add a document to the context
- [ ] Step 3: Search within the context
- [ ] Section: Common Use Cases (examples: project separation, topic organization)
- [ ] Section: Tips & Best Practices
- [ ] Section: Troubleshooting (common errors)

**Dependencies**: Task 7.2

---

## Summary

**Total Tasks**: 20
**Estimated Total Time**: 12-15 hours (1.5-2 days)

**Critical Path**:
1. Models (Tasks 1.1, 1.2) → 45 min
2. Services (Tasks 2.1, 2.2, 2.3) → 3.5 hours
3. Migration (Tasks 3.1, 3.2) → 1.5 hours
4. New Tools (Tasks 4.1-4.4) → 2 hours
5. Update Tools (Tasks 5.1-5.3) → 1.5 hours
6. Testing (Tasks 6.1-6.4) → 4 hours
7. Documentation (Tasks 7.1-7.3) → 1.25 hours

**Parallel Opportunities**:
- Task 7.1 (config) can be done anytime
- Task 6.1 (validation tests) can start after Task 1.1
- Tasks 4.1-4.4 (new tools) can be done in parallel
- Tasks 5.1-5.3 (update tools) can be done in parallel

---

**Status**: Tasks Defined ✅  
**Next Step**: Run `/speckit.implement` to execute tasks  
**Quality Gates**: All tests pass, ruff linting passes, manual validation complete
