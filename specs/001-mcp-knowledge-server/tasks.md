# Tasks: MCP Knowledge Server

**Input**: Design documents from `/specs/001-mcp-knowledge-server/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Per Constitution II (Testing Standards), comprehensive testing is required:
- Unit tests for business logic (minimum 70% coverage, 80% for critical paths)
- Integration tests for component interactions and API contracts
- End-to-end tests for critical user journeys
- All tests must pass before merge (Quality Gates)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (src/, tests/, docs/)
- [X] T002 Initialize Python project with pyproject.toml and setup.py
- [X] T003 [P] Create requirements.txt with all dependencies
- [X] T004 [P] Create default_config.yaml in src/config/
- [X] T005 [P] Configure linting tools (black, ruff, mypy) in pyproject.toml
- [X] T006 [P] Create .gitignore for Python project
- [X] T007 [P] Create pytest.ini for test configuration
- [X] T008 [P] Create README.md with project overview and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Create DocumentFormat enum in src/models/document.py
- [X] T010 [P] Create ProcessingStatus enum in src/models/document.py
- [X] T011 [P] Create ProcessingMethod enum in src/models/document.py
- [X] T012 [P] Create TaskStatus enum in src/models/document.py
- [X] T013 Create Settings class in src/config/settings.py with Pydantic validation
- [X] T014 Implement configuration loading from YAML and environment variables in src/config/settings.py
- [X] T015 Setup logging configuration in src/utils/logging_config.py
- [X] T016 Create base processor interface in src/processors/base.py
- [X] T017 Initialize ChromaDB client wrapper in src/services/vector_store.py
- [X] T018 Implement embedding model loading with caching in src/services/embedding_service.py
- [X] T019 Create file format validation utilities in src/utils/validation.py
- [X] T020 Implement text chunking strategy in src/utils/chunking.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Add Knowledge from Documents (Priority: P1) 🎯 MVP

**Goal**: Enable users to add documents to the knowledge base with automatic processing and embedding

**Independent Test**: Add a single PDF document via knowledge-add and verify it's stored using knowledge-status

### Tests for User Story 1 (MANDATORY per Constitution II) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T021 [P] [US1] Unit test for Document model validation in tests/unit/test_models/test_document.py
- [ ] T022 [P] [US1] Unit test for PDF processor in tests/unit/test_processors/test_pdf_processor.py
- [ ] T023 [P] [US1] Unit test for DOCX processor in tests/unit/test_processors/test_docx_processor.py
- [ ] T024 [P] [US1] Unit test for text extraction service in tests/unit/test_services/test_text_extractor.py
- [ ] T025 [P] [US1] Unit test for OCR service in tests/unit/test_services/test_ocr_service.py
- [ ] T026 [P] [US1] Unit test for processing strategy logic in tests/unit/test_services/test_processing_strategy.py
- [ ] T027 [P] [US1] Unit test for embedding generation in tests/unit/test_services/test_embedding_service.py
- [X] T028 [P] [US1] Integration test for add document workflow in tests/integration/test_knowledge_workflows.py

### Implementation for User Story 1

- [X] T029 [P] [US1] Create Document entity model in src/models/document.py
- [X] T030 [P] [US1] Create Embedding entity model in src/models/embedding.py
- [X] T031 [P] [US1] Create KnowledgeBase aggregate model in src/models/knowledge_base.py
- [X] T032 [P] [US1] Create ProcessingTask model in src/models/document.py
- [X] T033 [P] [US1] Implement PDF processor in src/processors/pdf_processor.py
- [X] T034 [P] [US1] Implement DOCX processor in src/processors/docx_processor.py
- [X] T035 [P] [US1] Implement PPTX processor in src/processors/pptx_processor.py
- [X] T036 [P] [US1] Implement XLSX processor in src/processors/xlsx_processor.py
- [X] T037 [P] [US1] Implement HTML processor in src/processors/html_processor.py
- [X] T038 [P] [US1] Implement image processor in src/processors/image_processor.py
- [X] T039 [US1] Implement text extractor service in src/services/text_extractor.py (depends on processors)
- [X] T040 [US1] Implement OCR service with Tesseract in src/services/ocr_service.py
- [X] T041 [US1] Implement processing strategy decision logic in src/services/processing_strategy.py
- [X] T042 [US1] Implement document processor orchestration in src/services/document_processor.py
- [X] T043 [US1] Implement vector store operations (add embeddings) in src/services/vector_store.py
- [X] T044 [US1] Implement knowledge service add_document method in src/services/knowledge_service.py
- [X] T045 [US1] Add async task queue management in src/services/knowledge_service.py
- [X] T046 [US1] Implement progress tracking for long operations in src/services/knowledge_service.py
- [X] T047 [US1] Add error handling and validation (per Constitution III - UX Consistency)
- [X] T048 [US1] Add logging and performance monitoring (per Constitution IV)
- [X] T049 [US1] Run linting and formatting (per Constitution I - Code Quality)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Search Knowledge Semantically (Priority: P2)

**Goal**: Enable semantic search over the knowledge base using natural language queries

**Independent Test**: Add 3-5 documents, perform semantic searches, and verify relevant results are returned

### Tests for User Story 2 (MANDATORY per Constitution II) ⚠️

- [X] T050 [P] [US2] Unit test for SearchResult model in tests/unit/test_models/test_search_result.py
- [X] T051 [P] [US2] Unit test for search query embedding in tests/unit/test_services/test_embedding_service.py
- [X] T052 [P] [US2] Unit test for vector similarity search in tests/unit/test_services/test_vector_store.py
- [X] T053 [P] [US2] Integration test for search workflow in tests/integration/test_knowledge_workflows.py

### Implementation for User Story 2

- [X] T054 [P] [US2] Create SearchResult entity model in src/models/search_result.py
- [ ] T055 [US2] Implement query embedding generation in src/services/embedding_service.py
- [ ] T056 [US2] Implement semantic search in vector store in src/services/vector_store.py
- [ ] T057 [US2] Implement knowledge service search method in src/services/knowledge_service.py
- [ ] T058 [US2] Add result ranking and relevance scoring in src/services/knowledge_service.py
- [ ] T059 [US2] Implement metadata filtering for search in src/services/vector_store.py
- [ ] T060 [US2] Add validation and error handling (per Constitution III)
- [ ] T061 [US2] Verify performance requirements (per Constitution IV - <2s for 1000+ docs)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Manage Knowledge Base (Priority: P3)

**Goal**: Enable viewing, removing, and clearing documents from the knowledge base

**Independent Test**: Add documents, view status, remove specific documents, verify they're no longer searchable

### Tests for User Story 3 (MANDATORY per Constitution II) ⚠️

- [X] T062 [P] [US3] Unit test for document listing in tests/unit/test_services/test_knowledge_service.py
- [X] T063 [P] [US3] Unit test for document removal in tests/unit/test_services/test_knowledge_service.py
- [X] T064 [P] [US3] Unit test for knowledge base clear in tests/unit/test_services/test_knowledge_service.py
- [X] T065 [P] [US3] Integration test for management operations in tests/integration/test_knowledge_workflows.py

### Implementation for User Story 3

- [ ] T066 [US3] Implement knowledge-show (list documents) in src/services/knowledge_service.py
- [ ] T067 [US3] Implement knowledge-remove (delete document) in src/services/knowledge_service.py
- [ ] T068 [US3] Implement knowledge-clear (delete all) in src/services/knowledge_service.py
- [ ] T069 [US3] Implement knowledge-status (statistics) in src/services/knowledge_service.py
- [ ] T070 [US3] Add confirmation prompts for destructive operations (per Constitution III)
- [ ] T071 [US3] Implement cascade deletion (remove embeddings when document removed)
- [ ] T072 [US3] Add validation and error handling (per Constitution III)
- [ ] T073 [US3] Verify accessibility requirements (per Constitution III)

**Checkpoint**: All core knowledge operations should now be independently functional

---

## Phase 6: User Story 4 - Integrate with AI Tools via MCP (Priority: P4)

**Goal**: Expose all knowledge operations through MCP protocol over HTTP streaming transport

**Independent Test**: Connect an MCP client and verify all knowledge operations work through the protocol

### Tests for User Story 4 (MANDATORY per Constitution II) ⚠️

- [X] T074 [P] [US4] Contract test for knowledge-add tool in tests/contract/test_mcp_tools.py
- [X] T075 [P] [US4] Contract test for knowledge-search tool in tests/contract/test_mcp_tools.py
- [X] T076 [P] [US4] Contract test for knowledge-remove tool in tests/contract/test_mcp_tools.py
- [X] T077 [P] [US4] Contract test for knowledge-show tool in tests/contract/test_mcp_tools.py
- [X] T078 [P] [US4] Contract test for knowledge-clear tool in tests/contract/test_mcp_tools.py
- [X] T079 [P] [US4] Contract test for knowledge-status tool in tests/contract/test_mcp_tools.py
- [X] T080 [P] [US4] Contract test for knowledge-task-status tool in tests/contract/test_mcp_tools.py
- [X] T081 [P] [US4] Integration test for MCP protocol compliance in tests/integration/test_mcp_protocol.py
- [X] T082 [P] [US4] Integration test for concurrent MCP connections in tests/integration/test_mcp_protocol.py

### Implementation for User Story 4

- [X] T083 [P] [US4] Define MCP tool schemas in src/mcp/tools.py
- [X] T084 [P] [US4] Implement HTTP streaming transport in src/mcp/transport.py
- [ ] T085 [US4] Implement MCP server with tool registration in src/mcp/server.py
- [ ] T086 [US4] Implement knowledge-add MCP tool handler in src/mcp/tools.py
- [ ] T087 [US4] Implement knowledge-search MCP tool handler in src/mcp/tools.py
- [ ] T088 [US4] Implement knowledge-remove MCP tool handler in src/mcp/tools.py
- [ ] T089 [US4] Implement knowledge-show MCP tool handler in src/mcp/tools.py
- [ ] T090 [US4] Implement knowledge-clear MCP tool handler in src/mcp/tools.py
- [ ] T091 [US4] Implement knowledge-status MCP tool handler in src/mcp/tools.py
- [ ] T092 [US4] Implement knowledge-task-status MCP tool handler in src/mcp/tools.py
- [ ] T093 [US4] Add progress notifications for async operations in src/mcp/server.py
- [ ] T094 [US4] Implement error handling and MCP error codes in src/mcp/server.py
- [ ] T095 [US4] Add connection pooling for concurrent clients in src/mcp/transport.py
- [ ] T096 [US4] Verify MCP 2025-06-18 specification compliance
- [ ] T097 [US4] Add validation and error handling (per Constitution III)
- [ ] T098 [US4] Verify performance requirements (per Constitution IV - <500ms p95)

**Checkpoint**: All user stories should now be independently functional with MCP access

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T099 [P] Create architecture.md documentation in docs/
- [ ] T100 [P] Create configuration.md documentation in docs/
- [ ] T101 [P] Create mcp-integration.md documentation in docs/
- [ ] T102 Code cleanup and refactoring across all modules
- [ ] T103 Performance optimization for search and indexing (verify Constitution IV targets)
- [ ] T104 [P] Additional unit tests for edge cases (target 80% coverage per Constitution II)
- [ ] T105 Security hardening and input validation (verify Quality Gates per Constitution)
- [ ] T106 Memory profiling and optimization (<2GB for 10K docs per Constitution IV)
- [ ] T107 Run quickstart.md validation with real MCP clients
- [ ] T108 Final integration testing with Claude Desktop
- [ ] T109 Final integration testing with GitHub Copilot
- [ ] T110 Final code quality checks (black, ruff, mypy per Constitution I)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories CAN proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P4)**: Depends on US1, US2, US3 being functional (wraps existing functionality in MCP protocol)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before MCP tool handlers
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1-3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Processors in US1 can all be developed in parallel
- MCP tool implementations in US4 can be developed in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for Document model validation in tests/unit/test_models/test_document.py"
Task: "Unit test for PDF processor in tests/unit/test_processors/test_pdf_processor.py"
Task: "Unit test for DOCX processor in tests/unit/test_processors/test_docx_processor.py"
Task: "Unit test for text extraction service in tests/unit/test_services/test_text_extractor.py"
Task: "Unit test for OCR service in tests/unit/test_services/test_ocr_service.py"

# Launch all processors for User Story 1 together:
Task: "Implement PDF processor in src/processors/pdf_processor.py"
Task: "Implement DOCX processor in src/processors/docx_processor.py"
Task: "Implement PPTX processor in src/processors/pptx_processor.py"
Task: "Implement XLSX processor in src/processors/xlsx_processor.py"
Task: "Implement HTML processor in src/processors/html_processor.py"
Task: "Implement image processor in src/processors/image_processor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo (Full MCP integration!)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently
4. Team tackles User Story 4 together (wraps all functionality)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Summary

**Total Tasks**: 110
- Phase 1 (Setup): 8 tasks
- Phase 2 (Foundational): 12 tasks
- Phase 3 (User Story 1 - Add Documents): 29 tasks (8 tests + 21 implementation)
- Phase 4 (User Story 2 - Search): 12 tasks (4 tests + 8 implementation)
- Phase 5 (User Story 3 - Manage): 12 tasks (4 tests + 8 implementation)
- Phase 6 (User Story 4 - MCP Integration): 25 tasks (9 tests + 16 implementation)
- Phase 7 (Polish): 12 tasks

**Parallel Opportunities**: 45+ tasks can run in parallel within their phases

**MVP Scope**: Phases 1-3 (User Story 1 only) = 49 tasks = Functional document ingestion and storage

**Independent Test Criteria**:
- US1: Add a PDF, verify storage with knowledge-status
- US2: Search added documents, verify relevant results
- US3: View, remove documents, verify operations
- US4: Connect MCP client, call all tools
