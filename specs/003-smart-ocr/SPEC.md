# Feature Specification: Smart OCR Implementation

**Feature ID**: 003-smart-ocr  
**Version**: 1.0  
**Status**: Draft  
**Created**: 2025-10-27  
**Last Updated**: 2025-10-27

---

## Executive Summary

### Problem Statement

The knowledge MCP server currently has basic OCR capabilities but lacks intelligent decision-making about when and how to apply OCR. When processing documents, the system may:

- Skip OCR on scanned PDFs that appear to have extractable text but actually contain only gibberish or minimal content
- Waste resources by running OCR on documents that already have high-quality text extraction
- Fail to process image-only or scan-only documents effectively
- Not provide visibility into whether OCR was used during document processing

This results in incomplete knowledge base indexing and poor search results for scanned documents.

### Proposed Solution

Implement a smart OCR system that automatically determines when OCR is needed and applies it intelligently:

1. **Text Quality Detection**: Analyze extracted text to detect if it's insufficient (too short, garbled, or missing)
2. **Automatic OCR Fallback**: When text extraction fails or produces poor results, automatically attempt OCR
3. **Async Processing**: Always process OCR operations asynchronously to avoid blocking
4. **Result Acceptance**: Accept all OCR results regardless of confidence score (per requirements: "Accept all results")
5. **File Cleanup**: Immediately clean up temporary files after processing
6. **Processing Visibility**: Track and report whether OCR was used for each document

### Success Criteria

1. Documents with no extractable text are successfully processed using OCR
2. Scan-only PDFs are fully indexed and searchable within the knowledge base
3. OCR processing completes asynchronously without blocking other operations
4. Users can determine which documents were processed using OCR via status queries
5. System correctly processes test documents including scan-only PDFs within 2 minutes per document
6. No temporary files remain after document processing completes

---

## Scope

### In Scope

- Automatic detection of when OCR is needed based on extracted text quality
- Fallback to OCR when text extraction produces insufficient results
- Asynchronous OCR processing for all documents
- Accepting and storing all OCR results regardless of confidence scores
- Immediate cleanup of temporary files created during OCR
- Tracking processing method (text extraction vs OCR) in document metadata
- Configuration option to force OCR regardless of text extraction results

### Out of Scope

- Training or fine-tuning OCR models
- Manual OCR confidence threshold adjustments (accept all results per requirements)
- Pre-processing images for better OCR quality (contrast, rotation, etc.)
- Multiple OCR engine support (stick with Tesseract)
- OCR language auto-detection (use configured default language)
- Selective file retention based on quality

---

## User Scenarios & Testing

### Scenario 1: Processing Scan-Only PDF

**Context**: User adds a scanned medical document PDF that contains only images of text pages

**Steps**:
1. User calls `knowledge-add` with scan-only PDF file path
2. System validates file and creates processing task
3. System attempts text extraction, gets empty or minimal text
4. System detects poor text quality and automatically triggers OCR
5. OCR processes document asynchronously
6. User calls `knowledge-task-status` to check progress
7. System reports "Processing with OCR" status
8. OCR completes and text is indexed
9. User calls `knowledge-status` to verify document was added

**Expected Outcome**: 
- Document is fully indexed and searchable
- Processing metadata indicates OCR was used
- No temporary files remain on disk
- Search queries return relevant chunks from the document

### Scenario 2: Processing PDF with Good Text Extraction

**Context**: User adds a native PDF with embedded text

**Steps**:
1. User calls `knowledge-add` with native PDF file
2. System validates file and creates processing task
3. System extracts text successfully
4. System detects sufficient text quality
5. System skips OCR and proceeds with text-based indexing
6. User calls `knowledge-show` to see document details

**Expected Outcome**:
- Document is indexed using extracted text
- Processing metadata indicates text extraction was used (not OCR)
- Processing completes faster than OCR path
- No temporary files created

### Scenario 3: Force OCR Mode

**Context**: User wants to use OCR even though PDF has extractable text

**Steps**:
1. User calls `knowledge-add` with `force_ocr=true` parameter
2. System validates file and creates processing task
3. System skips text extraction quality check
4. System immediately triggers OCR processing
5. OCR results override any extracted text
6. Document is indexed with OCR-extracted content

**Expected Outcome**:
- OCR is used regardless of text extraction availability
- Processing metadata indicates forced OCR mode
- All OCR results are accepted and stored

### Scenario 4: Testing with Medicaid Document

**Context**: Testing with the scan-only Medicaid HC doc list 2023.pdf

**Steps**:
1. Add document using `knowledge-add`
2. Monitor async task status during processing
3. Verify OCR is automatically triggered
4. Check that document is fully indexed
5. Perform test searches for known content
6. Verify no temp files remain

**Expected Outcome**:
- OCR processes all pages successfully
- Content is searchable in knowledge base
- Processing completes within expected timeframe
- Metadata correctly indicates OCR usage

---

## Assumptions

1. **OCR Engine**: Tesseract is already installed and configured in the environment
2. **Python Libraries**: pytesseract and PIL/Pillow are available dependencies
3. **Text Quality Heuristics**: Documents with less than 100 characters or less than 70% alphanumeric ratio indicate poor extraction and need OCR
4. **Language Default**: English (eng) is the default OCR language unless otherwise configured
5. **Image Formats**: PDF pages can be converted to images for OCR processing using existing libraries
6. **Processing Time**: OCR processing may take 30-120 seconds per page depending on complexity
7. **Confidence Threshold**: Per requirements, all OCR results are accepted regardless of confidence score
8. **Storage**: Sufficient disk space exists for temporary image files during processing
9. **Async Framework**: Existing asyncio infrastructure can handle OCR background tasks
10. **File System**: Temporary files can be written to system temp directory and cleaned up immediately after use

---

## Functional Requirements

### FR-001: Text Quality Detection

**Priority**: Must Have

The system must analyze extracted text to determine if OCR is needed.

**Acceptance Criteria**:
- Detect when extracted text has less than 100 characters
- Detect when extracted text has less than 70% alphanumeric characters (indicates gibberish)
- Return boolean decision: needs_ocr (true/false)
- Log detection decision with reasoning

**Business Value**: Ensures documents requiring OCR are identified automatically

---

### FR-002: Automatic OCR Fallback

**Priority**: Must Have

When text extraction produces insufficient results, the system must automatically attempt OCR.

**Acceptance Criteria**:
- Automatically trigger OCR when text quality check indicates insufficient text
- Convert PDF pages to images suitable for OCR processing
- Pass images to OCR service for text extraction
- Use OCR-extracted text instead of original extracted text
- Log OCR fallback decision and results

**Business Value**: Ensures scan-only documents are processed without manual intervention

---

### FR-003: Asynchronous OCR Processing

**Priority**: Must Have

All OCR operations must execute asynchronously to avoid blocking.

**Acceptance Criteria**:
- OCR processing runs in background async task
- Task status updates reflect "Processing with OCR" state
- System remains responsive during OCR processing
- Other documents can be added while OCR is running
- Task completion updates document status to COMPLETED

**Business Value**: Maintains system responsiveness while processing slow OCR operations

---

### FR-004: Accept All OCR Results

**Priority**: Must Have

The system must accept and store all OCR results regardless of confidence score.

**Acceptance Criteria**:
- No filtering based on confidence threshold
- All OCR-extracted text is stored and indexed
- Low-confidence results are included in search results
- Log confidence scores for informational purposes only (don't act on them)

**Business Value**: Ensures maximum content availability, allowing users to find partial or imperfect matches

---

### FR-005: Immediate File Cleanup

**Priority**: Must Have

Temporary files created during OCR must be deleted immediately after processing.

**Acceptance Criteria**:
- Temporary image files are deleted after OCR completes
- Cleanup occurs even if OCR fails (use try/finally pattern)
- No orphaned temp files remain after processing
- Cleanup is logged for audit purposes

**Business Value**: Prevents disk space accumulation from temporary files

---

### FR-006: Processing Method Tracking

**Priority**: Must Have

The system must track and expose which processing method was used for each document.

**Acceptance Criteria**:
- Document metadata includes processing_method field (TEXT_EXTRACTION or OCR)
- `knowledge-show` command displays processing method
- `knowledge-status` aggregates documents by processing method
- Processing method is searchable/filterable

**Business Value**: Provides visibility into document processing for debugging and analytics

---

### FR-007: Force OCR Configuration

**Priority**: Should Have

Users must be able to force OCR processing even when text extraction is available.

**Acceptance Criteria**:
- `knowledge-add` accepts optional `force_ocr` boolean parameter (default: false)
- When force_ocr=true, skip text quality check and go directly to OCR
- Processing metadata indicates forced OCR mode
- Configuration setting in config.yaml for default force_ocr behavior

**Business Value**: Allows users to override automatic detection for edge cases or quality concerns

---

### FR-008: PDF Page to Image Conversion

**Priority**: Must Have

The system must convert PDF pages to images for OCR processing.

**Acceptance Criteria**:
- Extract individual pages from PDF documents
- Convert pages to image format (PNG or JPEG) suitable for Tesseract
- Handle multi-page PDFs by processing each page sequentially
- Combine OCR results from all pages into single text output
- Handle conversion errors gracefully with appropriate logging

**Business Value**: Enables OCR processing of PDF documents

---

### FR-009: OCR Error Handling

**Priority**: Must Have

The system must handle OCR failures gracefully without crashing.

**Acceptance Criteria**:
- Catch and log OCR exceptions
- Mark document processing as FAILED if OCR fails
- Include error message in task status and document metadata
- Don't lose original extracted text if OCR fails after successful extraction
- Clean up temp files even when OCR fails

**Business Value**: Ensures system stability and preserves partial results

---

### FR-010: Testing with Scan-Only Documents

**Priority**: Must Have

The system must successfully process real-world scan-only documents (test case: Medicaid PDF).

**Acceptance Criteria**:
- Successfully process the Medicaid HC doc list 2023.pdf test document
- Extract searchable text from all pages
- Complete processing within 5 minutes
- Index all chunks in vector database
- Return relevant results for test search queries

**Business Value**: Validates solution works with real-world scan-only documents

---

## Non-Functional Requirements

### NFR-001: Performance

**Priority**: Should Have

OCR processing should complete within reasonable timeframes.

**Acceptance Criteria**:
- Single-page document OCR completes within 2 minutes
- Multi-page documents process at rate of 1-2 minutes per page
- System can process multiple OCR tasks concurrently (up to configured limit)
- OCR processing doesn't block text-extraction-only documents

**Business Value**: Ensures acceptable user experience for document processing

---

### NFR-002: Reliability

**Priority**: Must Have

OCR processing must be reliable and recoverable.

**Acceptance Criteria**:
- OCR failures don't crash the server
- Failed OCR tasks can be retried
- Partial results are preserved when possible
- System state remains consistent after OCR failures

**Business Value**: Ensures system stability and data integrity

---

### NFR-003: Observability

**Priority**: Should Have

OCR processing should be observable and debuggable.

**Acceptance Criteria**:
- Log OCR decisions (needs_ocr determination)
- Log OCR processing start, progress, and completion
- Log confidence scores (even though not used for filtering)
- Include processing method in response metadata
- Task status provides clear OCR progress information

**Business Value**: Enables debugging and performance monitoring

---

## Key Entities

### Document (Updated)

**Attributes**:
- `processing_method`: Enum (TEXT_EXTRACTION, OCR, IMAGE_ANALYSIS)
- `ocr_confidence`: Optional float (average confidence score if OCR was used)
- `force_ocr`: Boolean flag indicating if OCR was forced

**Relationships**:
- Links to ProcessingTask via document_id

### ProcessingTask (Updated)

**Attributes**:
- `ocr_used`: Boolean indicating if OCR was triggered
- `ocr_confidence`: Optional float if OCR was used
- `current_step`: Updated to include "Processing with OCR" status

### OCRConfig (New)

**Attributes**:
- `enabled`: Boolean (default: true)
- `language`: String (default: "eng")
- `force_ocr`: Boolean (default: false)
- `confidence_threshold`: Float (not used per requirements, kept for future)
- `temp_file_retention`: String (default: "immediate_cleanup")

---

## Configuration

### config.yaml Updates

```yaml
processing:
  ocr:
    enabled: true
    language: "eng"
    force_ocr: false
    # Confidence threshold not enforced per requirements
    confidence_threshold: 0.0  # Accept all results
    temp_file_retention: "immediate_cleanup"
```

---

## Success Metrics

1. **OCR Accuracy Rate**: Percentage of scan-only documents successfully processed
   - Target: 95% of scan-only documents fully indexed

2. **Processing Time**: Average time to process documents with OCR
   - Target: Under 2 minutes per page

3. **Automatic Detection Rate**: Percentage of times OCR is correctly triggered when needed
   - Target: 100% of documents with insufficient text trigger OCR

4. **Search Quality**: Relevance of search results for OCR-processed documents
   - Target: Test queries return expected chunks from scan-only documents

5. **File Cleanup**: Percentage of processing operations with zero temp files remaining
   - Target: 100% cleanup rate

6. **System Stability**: Server uptime during OCR processing
   - Target: Zero crashes or hangs due to OCR processing

---

## Dependencies

### Technical Dependencies

1. **Tesseract OCR**: System-level installation of tesseract-ocr package
2. **pytesseract**: Python wrapper for Tesseract
3. **pdf2image** or **pymupdf**: Library for converting PDF pages to images
4. **PIL/Pillow**: Image processing library

### Feature Dependencies

None - this is an enhancement to existing document processing

---

## Risks and Mitigations

### Risk 1: OCR Processing Time

**Description**: OCR may take too long for large multi-page documents

**Likelihood**: Medium  
**Impact**: Medium  
**Mitigation**: 
- Process asynchronously with clear progress indicators
- Consider page-level parallelization in future iterations
- Set reasonable timeout limits (5-10 minutes per document)

### Risk 2: Temporary File Accumulation

**Description**: Failed cleanup could fill disk space

**Likelihood**: Low  
**Impact**: High  
**Mitigation**:
- Use try/finally blocks for guaranteed cleanup
- Implement periodic orphaned file cleanup job
- Monitor disk space usage

### Risk 3: Poor OCR Quality

**Description**: OCR may produce gibberish or low-quality text

**Likelihood**: Medium  
**Impact**: Medium  
**Mitigation**:
- Accept all results per requirements (user knows some docs are scans)
- Log confidence scores for future quality analysis
- Consider pre-processing enhancements in future iterations

### Risk 4: Missing Dependencies

**Description**: Tesseract may not be installed in deployment environments

**Likelihood**: Low  
**Impact**: High  
**Mitigation**:
- Document installation requirements clearly
- Provide graceful degradation (warning instead of crash)
- Include dependency check in server startup

---

## Open Questions

None - requirements are clear based on user specifications:
- OCR Accuracy Handling: Accept all results
- Processing Mode: Always async
- File Cleanup: Immediate

---

## Appendix

### Test Document Details

**Medicaid HC doc list 2023.pdf**:
- Type: Scan-only PDF
- Expected Behavior: Automatic OCR trigger
- Success Criteria: Full text extraction and indexing
- Use Case: Validates real-world scan processing

### Processing Flow Diagram

```
Document Added
    ↓
Text Extraction Attempted
    ↓
Quality Check
    ├─ Good Text → Use Extracted Text → Index
    └─ Poor Text → Trigger OCR (Async)
                       ↓
                   Convert Pages to Images
                       ↓
                   Run Tesseract OCR
                       ↓
                   Accept All Results
                       ↓
                   Clean Up Temp Files
                       ↓
                   Index OCR Text
```

### Related Documentation

- [Tesseract Documentation](https://github.com/tesseract-ocr/tesseract)
- [pytesseract Library](https://pypi.org/project/pytesseract/)
- Existing OCR Service: `src/services/ocr_service.py`
- PDF Processor: `src/processors/pdf_processor.py`
