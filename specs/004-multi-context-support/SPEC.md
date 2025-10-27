# Feature Specification: Multi-Context Support

**Feature ID**: 004-multi-context-support  
**Version**: 1.0  
**Status**: Draft  
**Created**: 2025-10-27  
**Last Updated**: 2025-10-27

---

## Executive Summary

### Problem Statement

The current knowledge MCP server stores all documents in a single global knowledge base without any organizational structure. Users cannot:

- Organize documents into separate topical contexts (e.g., "AWS WAFR", "Medical Documents", "Financial Services")
- Search within a specific context to get more focused, relevant results
- Manage different knowledge domains separately while using the same server instance
- Add the same file to multiple contexts for different use cases
- Isolate search results to specific subject areas

This limitation makes the knowledge base increasingly difficult to navigate as more documents are added across different domains. Users must sift through irrelevant results from unrelated contexts when searching.

### Proposed Solution

Implement a multi-context system that allows users to:

1. **Create Named Contexts**: Define separate knowledge contexts (e.g., "aws-architecture", "healthcare-compliance", "project-x")
2. **Context-Scoped Document Addition**: Add documents to specific contexts with explicit context linking
3. **Context-Aware Search**: Search within a single context for focused results OR search across all contexts
4. **Context Management**: List, view, and manage contexts independently
5. **ChromaDB Schema Updates**: Extend the vector database schema to support context segmentation
6. **Default Context**: Provide a "default" context for backward compatibility when no context is specified

### Success Criteria

1. Users can create multiple named contexts and add documents to each
2. Documents can be added to multiple contexts simultaneously
3. Search within a specific context returns only results from that context
4. Search across all contexts aggregates results from the entire knowledge base
5. Context isolation prevents cross-contamination of search results
6. Existing documents migrate to "default" context automatically
7. API remains backward compatible - operations without context parameter use "default" context
8. ChromaDB collections properly segregate contexts using metadata filtering or collection-per-context strategy

---

## Scope

### In Scope

- Named context creation and management (create, list, describe, delete)
- Adding documents to one or more specified contexts
- Context-scoped search that filters results to specific context
- Cross-context search that queries all contexts
- ChromaDB schema updates to support context metadata or separate collections
- Migration of existing documents to "default" context
- Context parameter in knowledge-add, knowledge-search, and knowledge-show tools
- Context listing and statistics (document count, chunk count per context)
- Validation that context names follow naming conventions (alphanumeric, dashes, underscores)

### Out of Scope

- Context hierarchies or nested contexts (flat structure only)
- Context-level access control or permissions (all contexts are accessible)
- Context-specific embedding models (all contexts use the same model)
- Automatic context detection based on document content
- Context merging or splitting operations
- Context templates or presets
- Cross-context document deduplication

---

## User Scenarios & Testing

### Scenario 1: Creating and Using Separate Knowledge Contexts

**Context**: User manages AWS architecture documents and healthcare compliance documents separately

**Steps**:
1. User creates context "aws-architecture" using `knowledge-context-create` tool
2. User creates context "healthcare-compliance" using `knowledge-context-create` tool
3. User adds AWS WAFR PDF to "aws-architecture" context: `knowledge-add /path/to/wafr.pdf --context aws-architecture`
4. User adds Healthcare doc to "healthcare-compliance" context: `knowledge-add /path/to/medicaid.pdf --context healthcare-compliance`
5. User searches for "security pillar" in "aws-architecture" context: `knowledge-search "security pillar" --context aws-architecture`
6. Search returns only results from AWS WAFR document, not healthcare docs

**Expected Outcome**:
- Two distinct contexts exist with separate documents
- Context-scoped search returns only relevant results from specified context
- No cross-contamination between unrelated knowledge domains

### Scenario 2: Adding Document to Multiple Contexts

**Context**: User has a financial services compliance document relevant to both AWS and healthcare contexts

**Steps**:
1. User has existing contexts: "aws-architecture" and "healthcare-compliance"
2. User adds financial services lens document to both contexts: `knowledge-add /path/to/fin-services-lens.pdf --context aws-architecture,healthcare-compliance`
3. User searches in "aws-architecture" context - finds fin-services-lens results
4. User searches in "healthcare-compliance" context - finds same document
5. User lists documents in each context - sees document in both

**Expected Outcome**:
- Same document appears in multiple contexts
- Search results include the document when querying either context
- Document is stored once but linked to multiple contexts

### Scenario 3: Cross-Context Search

**Context**: User wants to search across all knowledge regardless of context

**Steps**:
1. User has documents in "aws-architecture", "healthcare-compliance", and "default" contexts
2. User performs search without specifying context: `knowledge-search "security best practices"`
3. System searches across ALL contexts
4. Results include documents from aws-architecture, healthcare-compliance, and default contexts
5. Result metadata indicates which context each result came from

**Expected Outcome**:
- Cross-context search aggregates results from all contexts
- User can see context information in search results
- Comprehensive results when context is unknown or irrelevant

### Scenario 4: Context Management

**Context**: User wants to view and manage their contexts

**Steps**:
1. User lists all contexts: `knowledge-context-list`
2. System shows all contexts with document counts and chunk counts
3. User gets details on specific context: `knowledge-context-show --context aws-architecture`
4. System shows all documents in that context with metadata
5. User deletes empty test context: `knowledge-context-delete --context test-context`

**Expected Outcome**:
- Users can view all contexts and their contents
- Context statistics are accurate
- Empty contexts can be deleted
- Deleting context doesn't delete documents (only context linkage)

### Scenario 5: Backward Compatibility

**Context**: Existing code/workflows that don't specify context continue working

**Steps**:
1. User adds document without specifying context: `knowledge-add /path/to/doc.pdf`
2. System automatically assigns to "default" context
3. User searches without specifying context: `knowledge-search "query"`
4. System searches across all contexts (including default)
5. Existing documents from before multi-context feature are in "default" context

**Expected Outcome**:
- All existing functionality works without modification
- "default" context serves as backward-compatible container
- No breaking changes to existing API

---

## Assumptions

1. **Flat Context Structure**: Contexts are not hierarchical; all contexts are at the same level
2. **No Access Control**: All users/sessions can access all contexts (authorization is out of scope)
3. **Same Embedding Model**: All contexts use the same embedding model configured for the server
4. **ChromaDB Collections**: Each context will be implemented as a separate ChromaDB collection for efficient filtering
5. **Context Naming**: Context names must be alphanumeric with dashes/underscores, max 64 characters
6. **Default Context**: Special "default" context is created automatically and cannot be deleted
7. **Document Storage**: Documents are stored once in the filesystem; contexts only affect vector DB organization
8. **Migration**: Existing documents automatically migrate to "default" context on first server start with new schema
9. **Search Performance**: Context-scoped search performs better than cross-context search due to smaller search space
10. **Context Deletion**: Deleting a context removes context metadata but doesn't delete source documents or their chunks from other contexts

---

## Functional Requirements

### FR-001: Create Named Context

**Priority**: Must Have

Users must be able to create named contexts for organizing documents.

**Acceptance Criteria**:
- API endpoint/tool for creating new context: `knowledge-context-create --name <context-name> --description <optional-description>`
- Context names must be unique (case-insensitive)
- Context names must match pattern: `^[a-zA-Z0-9_-]{1,64}$`
- System validates context name format and uniqueness
- System creates ChromaDB collection for the context
- System stores context metadata (name, description, created_at)
- Returns success confirmation with context details

**Business Value**: Enables users to organize knowledge into logical domains

---

### FR-002: List All Contexts

**Priority**: Must Have

Users must be able to view all available contexts.

**Acceptance Criteria**:
- API endpoint/tool: `knowledge-context-list`
- Returns list of all contexts with metadata
- Each context shows: name, description, document count, chunk count, created_at
- List sorted alphabetically by context name
- "default" context always appears in list

**Business Value**: Provides visibility into knowledge organization

---

### FR-003: View Context Details

**Priority**: Must Have

Users must be able to view detailed information about a specific context.

**Acceptance Criteria**:
- API endpoint/tool: `knowledge-context-show --context <context-name>`
- Returns context metadata and statistics
- Lists all documents in the context
- Shows total chunk count for context
- Shows embedding model used
- Returns error if context doesn't exist

**Business Value**: Enables users to understand context contents and scope

---

### FR-004: Delete Context

**Priority**: Should Have

Users must be able to delete unused contexts.

**Acceptance Criteria**:
- API endpoint/tool: `knowledge-context-delete --context <context-name> --confirm`
- Requires confirmation flag to prevent accidental deletion
- Cannot delete "default" context (returns error)
- Deletes ChromaDB collection for the context
- Removes context metadata
- Documents remain in other contexts they belong to
- Documents in ONLY the deleted context are removed from vector DB but source files remain
- Returns success confirmation

**Business Value**: Allows cleanup of obsolete knowledge organization structures

---

### FR-005: Add Document to Specific Context(s)

**Priority**: Must Have

Users must be able to add documents to one or more contexts.

**Acceptance Criteria**:
- `knowledge-add` tool accepts `--context` parameter
- Parameter accepts single context: `--context aws-architecture`
- Parameter accepts multiple contexts (comma-separated): `--context aws-architecture,healthcare-compliance`
- If no context specified, defaults to "default" context (backward compatibility)
- System validates all specified contexts exist (or creates them if auto-creation enabled)
- Document is indexed into ChromaDB collection for each specified context
- Returns error if any specified context doesn't exist and auto-creation is disabled
- Metadata tracks which contexts document belongs to

**Business Value**: Enables targeted knowledge organization and multi-domain document categorization

---

### FR-006: Search Within Specific Context

**Priority**: Must Have

Users must be able to search within a single context for focused results.

**Acceptance Criteria**:
- `knowledge-search` tool accepts `--context` parameter
- When context specified, search only queries that context's ChromaDB collection
- Returns only results from specified context
- Result metadata includes context name
- Returns error if specified context doesn't exist
- Performance improved compared to cross-context search (smaller search space)

**Business Value**: Provides focused, relevant search results within specific knowledge domains

---

### FR-007: Search Across All Contexts

**Priority**: Must Have

Users must be able to search across all contexts when context is not specified.

**Acceptance Criteria**:
- When no `--context` parameter provided, search queries all contexts
- System queries all ChromaDB collections (all contexts)
- Results aggregated from all contexts
- Each result's metadata indicates which context it came from
- Results remain ranked by relevance score across contexts
- Backward compatible with existing search behavior

**Business Value**: Enables comprehensive knowledge discovery when context is unknown

---

### FR-008: ChromaDB Schema for Multi-Context

**Priority**: Must Have

ChromaDB must support context isolation through collection-per-context strategy.

**Acceptance Criteria**:
- Each context has its own ChromaDB collection named `knowledge_<context-name>`
- Collection metadata includes context name and description
- Document chunks in each collection include document_id, chunk metadata
- Cross-context search aggregates results from multiple collections
- Collection creation/deletion managed automatically with context lifecycle
- Migration script creates collections from existing data

**Business Value**: Ensures efficient context isolation and search performance

---

### FR-009: Context Metadata Tracking

**Priority**: Must Have

System must track metadata for each context.

**Acceptance Criteria**:
- Context metadata stored in configuration or database
- Metadata includes: name, description, created_at, document_count, chunk_count
- Metadata updated when documents added/removed
- Metadata accessible via context-show API
- Statistics calculated efficiently without full collection scan

**Business Value**: Provides visibility and management capabilities for contexts

---

### FR-010: Migrate Existing Documents to Default Context

**Priority**: Must Have

Existing documents must migrate to "default" context automatically.

**Acceptance Criteria**:
- On first server start with multi-context feature, migration runs automatically
- All existing documents assigned to "default" context
- Existing ChromaDB collection renamed or migrated to `knowledge_default`
- Migration is idempotent (safe to run multiple times)
- Migration logged with success/failure status
- No data loss during migration

**Business Value**: Ensures backward compatibility and smooth upgrade path

---

### FR-011: Default Context Behavior

**Priority**: Must Have

System must provide "default" context for backward compatibility.

**Acceptance Criteria**:
- "default" context created automatically on server initialization
- Cannot be deleted
- Used automatically when no context specified in knowledge-add
- Existing functionality works without specifying context
- "default" appears in context list like any other context

**Business Value**: Maintains backward compatibility with existing workflows

---

### FR-012: Context Name Validation

**Priority**: Must Have

System must validate context names to ensure consistency and avoid errors.

**Acceptance Criteria**:
- Context names must match regex: `^[a-zA-Z0-9_-]{1,64}$`
- Names are case-insensitive unique (normalized to lowercase internally)
- Reserved name "default" cannot be created explicitly (auto-created only)
- Validation errors return clear messages indicating requirements
- Validation occurs before any ChromaDB operations

**Business Value**: Prevents naming conflicts and ensures system stability

---

## Non-Functional Requirements

### NFR-001: Performance

**Priority**: Should Have

Context operations must perform efficiently.

**Acceptance Criteria**:
- Context-scoped search completes 20-30% faster than cross-context search
- Context creation completes within 1 second
- Context listing completes within 2 seconds regardless of context count
- Adding document to multiple contexts adds minimal overhead (< 500ms per additional context)

**Business Value**: Ensures good user experience with multi-context operations

---

### NFR-002: Backward Compatibility

**Priority**: Must Have

Existing API functionality must continue working without modification.

**Acceptance Criteria**:
- All existing knowledge-add, knowledge-search, knowledge-show calls work without changes
- Operations without context parameter behave as before (use/search "default" context)
- Existing documents accessible after migration
- No breaking changes to MCP tool interfaces

**Business Value**: Protects existing user workflows and integrations

---

### NFR-003: Scalability

**Priority**: Should Have

System must scale to reasonable numbers of contexts and documents per context.

**Acceptance Criteria**:
- Support up to 100 contexts per server instance
- Each context can contain thousands of documents
- ChromaDB collection-per-context strategy scales linearly
- No performance degradation with up to 50 contexts

**Business Value**: Enables diverse use cases with multiple knowledge domains

---

## Key Entities

### Context (New)

**Attributes**:
- `name`: String, unique, lowercase normalized, 1-64 chars, alphanumeric with dashes/underscores
- `description`: Optional string describing context purpose
- `created_at`: Timestamp when context was created
- `document_count`: Integer, number of documents in context
- `chunk_count`: Integer, number of chunks in context's ChromaDB collection
- `collection_name`: String, ChromaDB collection name (e.g., `knowledge_aws-architecture`)

**Relationships**:
- One context has many documents (many-to-many relationship)
- One context has one ChromaDB collection

### Document (Updated)

**Attributes** (new):
- `contexts`: List of context names this document belongs to

**Relationships** (updated):
- Links to multiple contexts via contexts list

### ChromaDB Collection (Per Context)

**Structure**:
- Collection name pattern: `knowledge_<context-name>`
- Metadata: `{"context_name": "<name>", "context_description": "<desc>"}`
- Documents include: embeddings, chunk text, document_id, chunk metadata

---

## Configuration

### config.yaml Updates

```yaml
knowledge:
  contexts:
    default_context: "default"
    auto_create_contexts: false  # If true, creating non-existent context in knowledge-add creates it
    max_contexts: 100
    name_pattern: "^[a-zA-Z0-9_-]{1,64}$"
  
  # ChromaDB collection naming
  collection_prefix: "knowledge_"
```

---

## API Changes

### New Tools

#### knowledge-context-create
```json
{
  "name": "knowledge-context-create",
  "description": "Create a new knowledge context",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Context name (alphanumeric, dashes, underscores, 1-64 chars)"
      },
      "description": {
        "type": "string",
        "description": "Optional description of context purpose"
      }
    },
    "required": ["name"]
  }
}
```

#### knowledge-context-list
```json
{
  "name": "knowledge-context-list",
  "description": "List all knowledge contexts",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

#### knowledge-context-show
```json
{
  "name": "knowledge-context-show",
  "description": "Show details of a specific context",
  "inputSchema": {
    "type": "object",
    "properties": {
      "context": {
        "type": "string",
        "description": "Context name"
      }
    },
    "required": ["context"]
  }
}
```

#### knowledge-context-delete
```json
{
  "name": "knowledge-context-delete",
  "description": "Delete a context (cannot delete 'default')",
  "inputSchema": {
    "type": "object",
    "properties": {
      "context": {
        "type": "string",
        "description": "Context name to delete"
      },
      "confirm": {
        "type": "boolean",
        "description": "Confirmation flag"
      }
    },
    "required": ["context", "confirm"]
  }
}
```

### Updated Tools

#### knowledge-add (Updated)
```json
{
  "name": "knowledge-add",
  "inputSchema": {
    "properties": {
      "file_path": { "type": "string" },
      "metadata": { "type": "object" },
      "force_ocr": { "type": "boolean" },
      "context": {
        "type": "string",
        "description": "Comma-separated context names (e.g., 'aws-architecture,healthcare-compliance'). Defaults to 'default' if not specified."
      }
    }
  }
}
```

#### knowledge-search (Updated)
```json
{
  "name": "knowledge-search",
  "inputSchema": {
    "properties": {
      "query": { "type": "string" },
      "top_k": { "type": "integer" },
      "min_relevance": { "type": "number" },
      "context": {
        "type": "string",
        "description": "Context name to search within. If not specified, searches across all contexts."
      }
    }
  }
}
```

#### knowledge-show (Updated)
```json
{
  "name": "knowledge-show",
  "inputSchema": {
    "properties": {
      "limit": { "type": "integer" },
      "context": {
        "type": "string",
        "description": "Filter documents by context. If not specified, shows all documents across all contexts."
      }
    }
  }
}
```

---

## Success Metrics

1. **Context Adoption Rate**: Percentage of documents added to non-default contexts
   - Target: 60% of new documents use specific contexts within 1 month

2. **Search Precision Improvement**: Relevance of context-scoped vs. cross-context search
   - Target: Context-scoped search improves precision by 30%

3. **Context Organization**: Average number of contexts created per user
   - Target: Users create 3-5 contexts for different knowledge domains

4. **Performance Improvement**: Search speed improvement with context scoping
   - Target: 20-30% faster search in scoped contexts

5. **Backward Compatibility**: Zero regression in existing functionality
   - Target: 100% of existing tests pass after migration

6. **Migration Success**: Successful migration of existing documents
   - Target: 100% of existing documents accessible in "default" context

---

## Dependencies

### Technical Dependencies

1. **ChromaDB**: Must support multiple collections or efficient metadata filtering
2. **Existing Document Schema**: Must extend to include context relationships
3. **Migration Script**: Required for one-time migration of existing data

### Feature Dependencies

None - this is a new organizational feature built on existing infrastructure

---

## Risks and Mitigations

### Risk 1: ChromaDB Collection Limits

**Description**: ChromaDB might have performance issues with many collections

**Likelihood**: Low  
**Impact**: Medium  
**Mitigation**:
- Limit max contexts to 100 per configuration
- Monitor ChromaDB performance with multiple collections
- Have fallback plan to use metadata filtering within single collection if needed

### Risk 2: Migration Data Loss

**Description**: Migration could fail and lose existing documents

**Likelihood**: Low  
**Impact**: High  
**Mitigation**:
- Implement idempotent migration that can be re-run
- Create backup before migration
- Test migration on copy of production data
- Include rollback capability

### Risk 3: Context Naming Conflicts

**Description**: Users might create contexts with conflicting or reserved names

**Likelihood**: Medium  
**Impact**: Low  
**Mitigation**:
- Strict validation regex enforced at creation
- Case-insensitive uniqueness check
- Reserved name list (starting with just "default")
- Clear error messages guiding users to valid names

### Risk 4: Cross-Context Search Performance

**Description**: Searching all contexts might be slow with many contexts

**Likelihood**: Medium  
**Impact**: Medium  
**Mitigation**:
- Implement parallel query across collections
- Allow users to specify context for better performance
- Cache commonly accessed contexts
- Monitor and optimize as usage grows

### Risk 5: Backward Compatibility Break

**Description**: Changes might break existing API consumers

**Likelihood**: Low  
**Impact**: High  
**Mitigation**:
- All context parameters are optional
- Default behavior matches pre-multi-context behavior
- Comprehensive regression testing
- Clear migration documentation

---

## Open Questions

None - feature requirements are clear.

---

## Appendix

### Context Design Decision: Collections vs. Metadata

**Decision**: Use separate ChromaDB collection per context

**Rationale**:
- Better performance for context-scoped search (smaller search space)
- Natural isolation between contexts
- Easier to manage and delete contexts
- ChromaDB collections are designed for this use case

**Alternative Considered**: Single collection with context metadata filtering
- Would require filtering on every query
- Harder to get context statistics efficiently
- Potential for metadata filtering errors causing cross-contamination

### Migration Strategy

```
1. Detect first run with multi-context schema version
2. Create "default" context and ChromaDB collection
3. Migrate existing collection to knowledge_default
4. Update document metadata to include contexts: ["default"]
5. Create migration log entry
6. Server starts normally
```

### Example Usage Flow

```bash
# Create contexts
knowledge-context-create --name aws-architecture --description "AWS architecture and WAFR documents"
knowledge-context-create --name healthcare-compliance --description "Healthcare compliance and regulations"

# Add documents to contexts
knowledge-add /path/to/wafr.pdf --context aws-architecture
knowledge-add /path/to/medicaid.pdf --context healthcare-compliance
knowledge-add /path/to/fin-services-lens.pdf --context aws-architecture,healthcare-compliance

# Search within context
knowledge-search "security pillar" --context aws-architecture

# Search across all contexts
knowledge-search "compliance requirements"

# List contexts
knowledge-context-list

# View context details
knowledge-context-show --context aws-architecture

# Delete context
knowledge-context-delete --context test-context --confirm true
```

### Related Documentation

- ChromaDB Collections Documentation
- Existing Document Schema: `src/models/`
- Vector Store Service: `src/services/vector_store.py`
