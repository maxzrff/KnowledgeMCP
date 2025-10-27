# Implementation Plan: Smart OCR Implementation

**Branch**: `003-smart-ocr` | **Date**: 2025-10-27 | **Spec**: [SPEC.md](./SPEC.md)
**Input**: Feature specification from `/specs/003-smart-ocr/SPEC.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enhance the knowledge MCP server with intelligent OCR capabilities that automatically detect when OCR is needed and apply it effectively. The system will analyze extracted text quality, automatically fallback to OCR for scan-only documents, process OCR operations asynchronously, accept all OCR results regardless of confidence, implement immediate file cleanup, and track processing methods for visibility. Key features include text quality detection heuristics, PDF-to-image conversion for OCR, async processing with progress tracking, force OCR mode, and successful processing of real-world scan-only documents like medical records PDFs.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: 
- Tesseract OCR (system package: tesseract-ocr)
- pytesseract (Python wrapper for Tesseract)
- pdf2image or pymupdf (PDF page to image conversion)
- PIL/Pillow (image processing - already in dependencies)
- asyncio (async processing framework - stdlib)
- tempfile (temporary file management - stdlib)

**Storage**: Same as base feature - ChromaDB + filesystem (no new storage requirements)  
**Testing**: pytest with pytest-asyncio for async OCR operations, mock Tesseract for unit tests, real Tesseract for integration tests  
**Target Platform**: Cross-platform (Linux, macOS, Windows) - Tesseract must be installed on host  
**Project Type**: Enhancement to existing 001-mcp-knowledge-server feature  
**Performance Goals**: 
- Single-page OCR: <2 minutes per page
- Multi-page OCR: 1-2 minutes per page
- OCR processing doesn't block text-extraction documents
- Support concurrent OCR tasks (up to 3 simultaneous)

**Constraints**: 
- Accept ALL OCR results (no confidence filtering per requirements)
- Always use async processing mode for OCR
- Immediate cleanup of temp files (no retention)
- Tesseract must be pre-installed in environment
- Default language: English (eng)

**Scale/Scope**: 
- Handle multi-page documents (up to 1000 pages)
- Process scan-only PDFs like medical records
- Support concurrent OCR operations (3-5 simultaneous)
- Temp file size: ~5-10MB per page during processing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- **Code Quality Standards**: ✅ PASS
  - Linting: black, ruff, mypy (same as base feature)
  - Documentation: Docstrings for OCR service methods
  - Code follows single responsibility (OCR detection separate from OCR execution)
  
- **Testing Standards**: ✅ PASS
  - Target 80% coverage for OCR detection and processing logic
  - Unit tests for text quality detection heuristics
  - Integration tests with real Tesseract and scan-only PDFs
  - Mock Tesseract for fast unit tests
  - Test with real-world document (Medicaid HC doc list 2023.pdf)
  
- **User Experience Consistency**: ✅ PASS
  - Error messages: Clear OCR failure messages with suggestions
  - Progress indicators: "Processing with OCR" status in task tracking
  - Graceful degradation: OCR failure preserves original extracted text
  - Visibility: Processing method tracked in metadata
  
- **Performance Requirements**: ✅ PASS
  - OCR processing: <2 minutes per page target
  - Async execution: No blocking of main thread
  - Concurrent operations: Support 3-5 simultaneous OCR tasks
  - Monitoring: Log OCR decisions, timing, confidence scores

**Quality Gates**: All constitution gates addressed in this plan.

*No deviations from constitution principles - this is an enhancement that follows existing patterns.*

## Project Structure

### Documentation (this feature)

```text
specs/003-smart-ocr/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── clarifications/      # Phase 1 output (/speckit.plan command)
│   └── ocr-config.md    # OCR configuration details
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code Updates (repository root)

**New Files**:
```text
src/services/
├── ocr_service.py           # OCR processing service (ENHANCED)
│   ├── detect_text_quality()     # Text quality heuristics
│   ├── needs_ocr()               # Decision logic
│   ├── process_with_ocr()        # Async OCR execution
│   ├── convert_pdf_to_images()   # PDF page conversion
│   └── cleanup_temp_files()      # File cleanup

src/utils/
└── text_analysis.py         # Text quality analysis utilities
    ├── calculate_alphanumeric_ratio()
    ├── detect_gibberish()
    └── estimate_readability()
```

**Modified Files**:
```text
src/processors/
└── pdf_processor.py         # Add OCR fallback logic
    └── extract_text() → enhanced with quality check + OCR fallback

src/models/
└── document.py              # Add processing_method field
    └── ProcessingMethod enum (TEXT_EXTRACTION, OCR, IMAGE_ANALYSIS)

src/config/
└── settings.py              # Add OCR configuration
    └── OCRConfig class

config.yaml                  # Add ocr section
```

**Test Files**:
```text
tests/unit/
├── test_ocr_service.py      # OCR service unit tests
├── test_text_analysis.py    # Text quality detection tests
└── test_pdf_processor.py    # Enhanced with OCR tests

tests/integration/
├── test_ocr_workflow.py     # End-to-end OCR processing
└── test_scan_documents.py   # Real scan-only document tests

tests/fixtures/
└── documents/
    ├── scan_only.pdf        # Test scan-only PDF
    └── medicaid_sample.pdf  # Medicaid document sample
```

**Structure Decision**: Enhancement to existing structure. OCR service already exists but needs significant enhancement. New text analysis utilities separate concerns. Minimal changes to existing processors and models - just add OCR fallback logic and metadata tracking.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. This enhancement follows all existing patterns and quality standards from the base feature.

---

## Phase 0: Research

**Objective**: Understand OCR integration patterns, text quality detection heuristics, and async processing strategies.

### Research Tasks

1. **OCR Integration Patterns**
   - **Goal**: Understand best practices for integrating Tesseract OCR with Python async code
   - **Method**: Review pytesseract documentation, async patterns for subprocess execution
   - **Output**: Document OCR execution patterns in `research.md`
   - **Decision Point**: Choose between pdf2image vs pymupdf for PDF-to-image conversion

2. **Text Quality Detection**
   - **Goal**: Research heuristics for detecting poor-quality extracted text
   - **Method**: Review academic papers on text quality metrics, analyze scan vs native PDF samples
   - **Output**: Document quality detection heuristics in `research.md`
   - **Decision Point**: Define thresholds (character count, alphanumeric ratio, etc.)

3. **Async OCR Processing**
   - **Goal**: Determine best approach for async OCR execution without blocking
   - **Method**: Research asyncio executor patterns, subprocess management, task cancellation
   - **Output**: Document async patterns in `research.md`
   - **Decision Point**: Choose execution strategy (ThreadPoolExecutor vs ProcessPoolExecutor)

4. **Temporary File Management**
   - **Goal**: Ensure reliable cleanup of temporary files even on failures
   - **Method**: Review Python tempfile module, context managers, try/finally patterns
   - **Output**: Document cleanup patterns in `research.md`
   - **Decision Point**: Use tempfile.TemporaryDirectory vs manual cleanup

5. **Real-World Test Document Analysis**
   - **Goal**: Understand characteristics of scan-only documents like Medicaid PDF
   - **Method**: Analyze Medicaid HC doc list 2023.pdf structure, page count, image quality
   - **Output**: Document test expectations in `research.md`
   - **Decision Point**: Define success criteria for test document

### Research Deliverables

**File**: `specs/003-smart-ocr/research.md`

**Required Sections**:
1. **OCR Integration Patterns**
   - pytesseract async execution patterns
   - PDF-to-image conversion library comparison (pdf2image vs pymupdf)
   - Error handling strategies

2. **Text Quality Heuristics**
   - Character count thresholds
   - Alphanumeric ratio analysis
   - Gibberish detection techniques
   - Edge cases (multilingual, mixed content)

3. **Async Processing Strategies**
   - ThreadPoolExecutor vs ProcessPoolExecutor comparison
   - Task cancellation and timeout handling
   - Progress tracking for long-running OCR

4. **Temporary File Management**
   - tempfile.TemporaryDirectory usage
   - Cleanup guarantees with try/finally
   - Disk space monitoring

5. **Test Document Analysis**
   - Medicaid PDF characteristics
   - Expected OCR output
   - Performance expectations

**Key Decision Records**:
- PDF-to-image conversion library choice
- Text quality threshold values
- Async execution strategy
- Temp file cleanup approach

---

## Phase 1: Design

**Objective**: Design OCR detection logic, async processing flow, and configuration model.

### Design Tasks

1. **OCR Detection Logic**
   - **Goal**: Design text quality analysis and OCR decision algorithm
   - **Artifacts**: 
     - Flow diagram in `data-model.md`
     - Pseudocode for quality detection
   - **Validation**: Edge cases covered (empty text, minimal text, gibberish)

2. **Async OCR Processing Flow**
   - **Goal**: Design end-to-end async OCR processing workflow
   - **Artifacts**:
     - Sequence diagram in `data-model.md`
     - Task state transitions
   - **Validation**: No deadlocks, proper error propagation

3. **Configuration Model**
   - **Goal**: Design OCR configuration structure and defaults
   - **Artifacts**:
     - OCRConfig class definition in `data-model.md`
     - config.yaml schema in `clarifications/ocr-config.md`
   - **Validation**: All requirements covered (force_ocr, language, cleanup mode)

4. **Data Model Updates**
   - **Goal**: Define updates to Document and ProcessingTask models
   - **Artifacts**:
     - Updated entity diagrams in `data-model.md`
     - Field definitions and relationships
   - **Validation**: Backward compatibility maintained

5. **API Surface**
   - **Goal**: Define changes to knowledge-add tool parameters
   - **Artifacts**:
     - Updated tool schema in `data-model.md`
     - Parameter validation rules
   - **Validation**: MCP specification compliance

### Design Deliverables

**File 1**: `specs/003-smart-ocr/data-model.md`

**Required Sections**:
1. **Entity Updates**
   - Document model with processing_method field
   - ProcessingTask model with ocr_used flag
   - OCRConfig configuration model

2. **OCR Detection Algorithm**
   - Text quality analysis logic
   - Decision tree for OCR trigger
   - Pseudocode implementation

3. **Async Processing Flow**
   - Sequence diagram: document add → OCR → indexing
   - Task state transitions
   - Error handling paths

4. **API Changes**
   - Updated knowledge-add tool parameters
   - Response metadata additions
   - Status query enhancements

5. **Configuration Schema**
   - OCRConfig fields and defaults
   - config.yaml structure
   - Environment variable overrides

**File 2**: `specs/003-smart-ocr/clarifications/ocr-config.md`

**Content**:
- Detailed config.yaml OCR section documentation
- Configuration examples for different use cases
- Migration guide from existing config

### Design Review Gates

- [ ] Text quality thresholds validated with sample documents
- [ ] Async flow handles all error scenarios
- [ ] Configuration model supports all requirements
- [ ] Data model changes are backward compatible
- [ ] API changes maintain MCP specification compliance

---

## Phase 2: Implementation

**Objective**: Implement OCR detection, async processing, and file cleanup with tests.

**Note**: Detailed task breakdown will be generated by `/speckit.tasks` command after Phase 1 completion.

### Implementation Workstreams

#### Workstream 1: Text Quality Detection
**Estimated Effort**: 4-6 hours  
**Files**: `src/utils/text_analysis.py`, tests  
**Dependencies**: None

**Tasks** (high-level):
1. Implement character count analysis
2. Implement alphanumeric ratio calculation
3. Implement gibberish detection
4. Add comprehensive unit tests
5. Document heuristics in code comments

**Validation**:
- [ ] Correctly identifies scan-only PDFs
- [ ] Correctly identifies native PDFs with good text
- [ ] Edge cases handled (empty, minimal, mixed content)
- [ ] 95%+ test coverage

#### Workstream 2: PDF-to-Image Conversion
**Estimated Effort**: 4-6 hours  
**Files**: `src/services/ocr_service.py`, tests  
**Dependencies**: Workstream 1

**Tasks** (high-level):
1. Implement PDF page extraction
2. Implement image conversion
3. Add temp file management with cleanup
4. Handle multi-page PDFs
5. Add integration tests with real PDFs

**Validation**:
- [ ] Converts PDFs to images successfully
- [ ] Handles multi-page documents
- [ ] Cleans up temp files reliably
- [ ] Works with various PDF types (scan, native, mixed)

#### Workstream 3: Async OCR Processing
**Estimated Effort**: 6-8 hours  
**Files**: `src/services/ocr_service.py`, tests  
**Dependencies**: Workstream 2

**Tasks** (high-level):
1. Implement async OCR execution with executor
2. Add progress tracking for long operations
3. Implement timeout and cancellation handling
4. Add error recovery and logging
5. Test with real Tesseract OCR

**Validation**:
- [ ] OCR runs asynchronously without blocking
- [ ] Progress tracking works correctly
- [ ] Timeouts trigger appropriately
- [ ] Errors handled gracefully
- [ ] All OCR results accepted (no confidence filtering)

#### Workstream 4: PDF Processor Integration
**Estimated Effort**: 4-6 hours  
**Files**: `src/processors/pdf_processor.py`, tests  
**Dependencies**: Workstream 1, 3

**Tasks** (high-level):
1. Add text quality check after extraction
2. Implement OCR fallback logic
3. Update metadata with processing method
4. Add force_ocr parameter support
5. Update tests with OCR scenarios

**Validation**:
- [ ] Automatically triggers OCR for scan-only PDFs
- [ ] Skips OCR for native PDFs with good text
- [ ] force_ocr parameter works correctly
- [ ] Processing method tracked in metadata

#### Workstream 5: Configuration & MCP Integration
**Estimated Effort**: 3-4 hours  
**Files**: `src/config/settings.py`, `config.yaml`, tests  
**Dependencies**: Workstream 4

**Tasks** (high-level):
1. Add OCRConfig model
2. Update config.yaml with OCR section
3. Add force_ocr parameter to knowledge-add tool
4. Update MCP tool responses with processing method
5. Update documentation

**Validation**:
- [ ] Configuration loads correctly
- [ ] force_ocr parameter propagates through system
- [ ] MCP responses include processing method
- [ ] Backward compatibility maintained

#### Workstream 6: Real-World Testing
**Estimated Effort**: 4-6 hours  
**Files**: Integration tests, test fixtures  
**Dependencies**: All previous workstreams

**Tasks** (high-level):
1. Add Medicaid PDF test fixture
2. Implement end-to-end OCR test
3. Validate search results from OCR content
4. Performance testing (timing, memory)
5. Document test results

**Validation**:
- [ ] Medicaid PDF processes successfully
- [ ] OCR completes within 5 minutes
- [ ] Content is searchable
- [ ] No temp files remain after processing
- [ ] Memory usage acceptable

### Implementation Estimates

| Workstream | Effort | Dependencies | Risk |
|------------|--------|--------------|------|
| 1. Text Quality Detection | 4-6h | None | Low |
| 2. PDF-to-Image Conversion | 4-6h | WS1 | Low |
| 3. Async OCR Processing | 6-8h | WS2 | Medium |
| 4. PDF Processor Integration | 4-6h | WS1,WS3 | Low |
| 5. Configuration & MCP | 3-4h | WS4 | Low |
| 6. Real-World Testing | 4-6h | All | Medium |
| **Total** | **25-36h** | | |

**Total Estimate**: 25-36 hours (~4-6 days of focused development)

### Testing Strategy

**Unit Tests** (70% coverage target):
- Text quality detection functions
- PDF-to-image conversion
- OCR service methods (mocked Tesseract)
- Configuration loading

**Integration Tests** (key workflows):
- End-to-end scan-only PDF processing
- Native PDF skips OCR
- Force OCR mode
- Concurrent OCR tasks
- Error scenarios (OCR failure, temp file cleanup failure)

**Real-World Tests**:
- Medicaid HC doc list 2023.pdf processing
- Multi-page document handling
- Performance benchmarks

**Test Environment**:
- Tesseract OCR must be installed
- Test fixtures in tests/fixtures/documents/
- Mock Tesseract for fast unit tests
- Real Tesseract for integration tests

---

## Phase 3: Quality Assurance

**Objective**: Validate OCR functionality, performance, and reliability.

### QA Activities

1. **Functional Testing**
   - Test all scenarios from SPEC.md
   - Verify text quality detection accuracy
   - Validate OCR fallback triggers correctly
   - Test force_ocr parameter
   - Verify processing method tracking

2. **Performance Testing**
   - Measure OCR processing time per page
   - Test concurrent OCR operations
   - Validate no blocking of text-extraction documents
   - Memory usage monitoring

3. **Reliability Testing**
   - Test OCR failure scenarios
   - Verify temp file cleanup in all cases
   - Test system stability during long OCR operations
   - Validate error recovery

4. **Integration Testing**
   - Test with various PDF types (scan, native, mixed)
   - Test with real-world documents
   - Validate search quality for OCR content
   - Test MCP tool integration

5. **Documentation Review**
   - Verify README updates
   - Check configuration documentation
   - Validate example usage
   - Review error message clarity

### QA Deliverables

1. **Test Results Report**
   - Test coverage metrics
   - Performance benchmarks
   - Known issues and limitations

2. **Documentation Updates**
   - README.md with OCR feature description
   - Configuration guide updates
   - Troubleshooting section for OCR issues

---

## Phase 4: Deployment

**Objective**: Deploy smart OCR feature to production.

### Deployment Tasks

1. **Dependency Installation**
   - Document Tesseract installation requirements
   - Add pytesseract and pdf2image to requirements.txt
   - Update installation instructions in README

2. **Configuration Migration**
   - Provide default OCR configuration
   - Document configuration options
   - Migration guide for existing installations

3. **Monitoring Setup**
   - Add OCR performance logging
   - Monitor temp file cleanup
   - Track OCR vs text extraction usage

4. **Rollout**
   - Merge feature branch to main
   - Update version number
   - Tag release

### Deployment Checklist

- [ ] Tesseract installation documented
- [ ] requirements.txt updated
- [ ] config.yaml includes OCR section
- [ ] README.md updated with OCR feature
- [ ] Tests passing (including real-world tests)
- [ ] Documentation complete
- [ ] Performance benchmarks acceptable
- [ ] Code reviewed and approved
- [ ] Feature branch merged to main
- [ ] Release tagged

---

## Risk Management

### Risk: OCR Processing Time
**Likelihood**: Medium | **Impact**: Medium  
**Mitigation**: 
- Async processing with clear progress indicators
- Timeout limits (5-10 minutes per document)
- Concurrent processing limits (3-5 simultaneous)
- **Monitoring**: Log OCR timing metrics

### Risk: Temporary File Accumulation
**Likelihood**: Low | **Impact**: High  
**Mitigation**:
- Use try/finally for guaranteed cleanup
- tempfile.TemporaryDirectory for automatic cleanup
- Monitor disk usage
- **Monitoring**: Log cleanup operations and failures

### Risk: Poor OCR Quality
**Likelihood**: Medium | **Impact**: Medium  
**Mitigation**:
- Accept all results per requirements
- Log confidence scores for analysis
- Document OCR usage in metadata
- **Monitoring**: Track OCR confidence scores

### Risk: Missing Tesseract Dependency
**Likelihood**: Low | **Impact**: High  
**Mitigation**:
- Document installation clearly
- Check dependency on server startup
- Graceful degradation with clear error message
- **Monitoring**: Log OCR availability on startup

---

## Success Criteria

### Functional Success
- [ ] Scan-only PDFs processed successfully with OCR
- [ ] Native PDFs skip OCR and use text extraction
- [ ] force_ocr parameter works correctly
- [ ] Processing method tracked in metadata
- [ ] All OCR results accepted (no filtering)
- [ ] Temp files cleaned up immediately
- [ ] Medicaid test document processes successfully

### Performance Success
- [ ] OCR processing <2 minutes per page
- [ ] Concurrent OCR operations supported (3-5 simultaneous)
- [ ] No blocking of text-extraction documents
- [ ] Memory usage acceptable (<2GB for 10K documents)

### Quality Success
- [ ] 80%+ test coverage for OCR code
- [ ] All integration tests passing
- [ ] Real-world test document passes
- [ ] Documentation complete and accurate
- [ ] Code review approved

### User Experience Success
- [ ] Clear progress indicators during OCR
- [ ] Helpful error messages for OCR failures
- [ ] Processing method visible in status queries
- [ ] Configuration options documented

---

## Timeline

**Total Duration**: 4-6 days of focused development

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 0: Research | 1 day | research.md |
| Phase 1: Design | 1 day | data-model.md, clarifications/ |
| Phase 2: Implementation | 4-6 days | Code + tests |
| Phase 3: QA | 1 day | Test results, docs |
| Phase 4: Deployment | 0.5 day | Merged to main |

**Milestone Schedule**:
- Day 1: Research and design complete
- Day 2-3: Core OCR implementation
- Day 4-5: Integration and testing
- Day 6: QA and deployment

---

## Appendix

### Related Features
- 001-mcp-knowledge-server (base feature)

### Key Technologies
- Tesseract OCR
- pytesseract
- pdf2image or pymupdf
- asyncio
- tempfile

### Test Documents
- Medicaid HC doc list 2023.pdf (scan-only, real-world)
- Sample scan-only PDF (created for tests)
- Sample native PDF with good text
- Sample mixed PDF (scan + native pages)

### Configuration Example

```yaml
processing:
  ocr:
    enabled: true
    language: "eng"
    force_ocr: false
    confidence_threshold: 0.0  # Accept all results
    temp_file_retention: "immediate_cleanup"
```

### Monitoring Metrics
- OCR processing time per page
- OCR vs text extraction usage ratio
- Temp file cleanup success rate
- OCR failure rate
- Average confidence scores
