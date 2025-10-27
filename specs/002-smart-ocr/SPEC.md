# Feature Specification: Smart OCR Implementation

**Feature ID**: 002-smart-ocr
**Status**: Draft
**Created**: 2025-10-27
**Last Updated**: 2025-10-27

---

## Overview

### Feature Summary

Implement intelligent OCR (Optical Character Recognition) as a fallback mechanism for PDF documents when standard text extraction yields no results. The system should automatically detect when a PDF contains only scanned images without embedded text and seamlessly invoke OCR processing without user intervention.

### Business Value

- **User Experience**: Enables processing of scanned documents without manual conversion steps
- **Coverage**: Expands supported document types to include legacy scanned PDFs
- **Automation**: Reduces manual preprocessing requirements for document ingestion
- **Data Accessibility**: Unlocks knowledge trapped in image-only PDFs

### Target Users

- Knowledge base administrators importing scanned documents
- Users with legacy document archives containing scanned PDFs
- Organizations digitizing paper-based documentation

---

## Problem Statement

### Current Situation

The knowledge MCP server currently uses pdfplumber for text extraction from PDFs. When processing scanned PDFs (images embedded in PDF format without text layers), the extraction returns empty or minimal text, causing the document to be ingested with no searchable content.

### Pain Points

1. Users must manually identify scan-only PDFs before ingestion
2. Scanned documents fail silently or produce empty knowledge base entries
3. No feedback mechanism indicates when OCR would be beneficial
4. Users must use external tools to convert scanned PDFs before ingestion

### Desired Outcome

The system automatically detects when PDF text extraction produces insufficient results and transparently applies OCR processing, providing users with fully searchable content from all PDF types.

---

## User Scenarios & Testing

### Primary Scenarios

#### Scenario 1: Scanned Medical Records Processing
**Actor**: Healthcare administrator
**Preconditions**: User has scanned patient records in PDF format
**Flow**:
1. User uploads scanned medical document PDF via `knowledge-add` command
2. System attempts standard text extraction
3. System detects no extractable text (0 characters or whitespace only)
4. System automatically invokes OCR processing on PDF pages
5. System extracts text from scanned images
6. System ingests document with OCR-extracted content
7. User receives confirmation with processing method indicator (OCR used)

**Expected Result**: Document is fully searchable despite being scan-only

#### Scenario 2: Mixed Content PDF
**Actor**: Financial services analyst
**Preconditions**: PDF contains both native text pages and scanned attachment pages
**Flow**:
1. User uploads financial services lens document
2. System extracts text from native text pages successfully
3. System detects pages 25-30 return no text
4. System applies OCR selectively to scan-only pages
5. System combines extracted and OCR'd text
6. User queries information from both native and scanned sections

**Expected Result**: All content is searchable regardless of page format

#### Scenario 3: High-Quality Native PDF
**Actor**: IT architect
**Preconditions**: User uploads AWS Well-Architected Framework PDF with embedded text
**Flow**:
1. User uploads native PDF document
2. System extracts text using standard method
3. System detects sufficient text content (> 100 characters)
4. System skips OCR processing (not needed)
5. System ingests document with standard text extraction

**Expected Result**: Fast processing without unnecessary OCR overhead

### Edge Cases

#### Edge Case 1: Password-Protected PDF
- System should detect access restrictions before attempting extraction
- Clear error message indicating password protection prevents processing
- No OCR attempt on inaccessible content

#### Edge Case 2: Corrupted PDF File
- System validates PDF structure before processing
- Appropriate error handling for malformed files
- No infinite OCR retry loops

#### Edge Case 3: Extremely Large Scanned PDF (500+ pages)
- System provides progress indicators for long-running OCR operations
- Processing occurs asynchronously with task tracking
- User receives task ID for status checking

---

## Functional Requirements

### Core Requirements

**REQ-OCR-001: Automatic Text Extraction Detection**
- System MUST attempt standard text extraction first using existing pdfplumber logic
- System MUST measure text extraction results (character count, word count)
- System MUST determine if extraction was successful based on configurable threshold
- Default threshold: Minimum 100 non-whitespace characters OR 20 words

**REQ-OCR-002: OCR Fallback Trigger**
- System MUST automatically invoke OCR when text extraction falls below threshold
- System MUST NOT require user configuration or explicit OCR request
- System MUST log decision to use OCR with reason (insufficient text extracted)

**REQ-OCR-003: OCR Processing**
- System MUST support OCR processing of PDF pages as images
- System MUST handle multi-page PDF documents
- System MUST preserve page order in OCR output
- System MUST support common PDF page sizes and orientations

**REQ-OCR-004: Processing Method Tracking**
- System MUST record which processing method was used (standard extraction vs OCR)
- System MUST expose processing method in document metadata
- System MUST include processing method in API responses
- User MUST be able to see if OCR was applied via `knowledge-show` command

**REQ-OCR-005: Error Handling**
- System MUST gracefully handle OCR failures
- System MUST return extracted text even if OCR fails on some pages
- System MUST log OCR errors with specific page numbers
- System MUST not fail entire document ingestion if OCR fails

**REQ-OCR-006: Performance Optimization**
- System MUST process OCR asynchronously for documents > 10 pages
- System MUST provide task ID for async OCR operations
- System MUST allow users to check OCR processing status via `knowledge-task-status`

**REQ-OCR-007: Hybrid Processing**
- System MUST support mixed-mode documents (some pages with text, some scanned)
- System MUST apply OCR only to pages with insufficient text
- System MUST combine text from both extraction methods into single document

### Configuration Requirements

**REQ-OCR-CFG-001: OCR Enable/Disable**
- System MUST allow OCR feature to be enabled/disabled via configuration
- Default: OCR enabled
- Configuration key: `ocr.enabled` in config.yaml

**REQ-OCR-CFG-002: Text Extraction Threshold**
- System MUST allow configuration of minimum character threshold
- Configuration key: `ocr.text_threshold_chars`
- Default value: 100
- Valid range: 0-10000

**REQ-OCR-CFG-003: OCR Engine Selection**
- System MUST allow selection of OCR engine via configuration
- Initial implementation: Tesseract OCR
- Configuration key: `ocr.engine`
- Default value: "tesseract"

**REQ-OCR-CFG-004: Language Configuration**
- System MUST support OCR language specification
- Configuration key: `ocr.languages`
- Default value: ["eng"]
- Support: Multiple language codes for multilingual documents

---

## Non-Functional Requirements

### Performance

- OCR processing MUST complete within 2 seconds per page for standard resolution (300 DPI)
- Async OCR operations MUST provide status updates at minimum every 10 seconds
- OCR processing MUST NOT block standard text extraction operations

### Scalability

- System MUST support concurrent OCR processing for multiple documents
- System MUST handle PDFs up to 1000 pages without memory overflow
- System MUST limit concurrent OCR operations to configured maximum (default: 3)

### Reliability

- OCR failure rate MUST be < 5% for standard quality scans (200+ DPI)
- System MUST maintain 99% uptime during OCR operations
- Failed OCR attempts MUST NOT corrupt document metadata

### Security

- OCR processing MUST occur in sandboxed environment (same security context as PDF processing)
- Temporary image files created during OCR MUST be deleted after processing
- OCR libraries MUST NOT transmit document content to external services

---

## Success Criteria

### Measurable Outcomes

1. **Functional Completeness**
   - 100% of scan-only PDFs produce searchable text (where scan quality permits)
   - Mixed-mode PDFs successfully combine extracted and OCR'd content
   - Processing method correctly recorded for 100% of documents

2. **User Experience**
   - Users successfully process scanned PDFs without manual intervention
   - OCR processing completes within 5 minutes for 100-page documents
   - Status tracking available for all async OCR operations

3. **System Performance**
   - OCR adds < 10% overhead to standard PDF processing time
   - Zero system crashes or memory leaks during OCR operations
   - Successful processing of 95%+ of uploaded scanned PDFs

4. **Quality Metrics**
   - OCR accuracy > 95% for machine-printed text at 300 DPI
   - OCR accuracy > 85% for machine-printed text at 200 DPI
   - Properly handled error cases (corrupted PDFs, unsupported formats)

### Verification Methods

- Unit tests for text extraction threshold detection
- Integration tests with sample scanned PDFs (medical records, financial documents)
- Performance benchmarks comparing standard vs OCR processing times
- Manual verification of OCR output quality on real-world documents

---

## Key Entities & Attributes

### ProcessingMethod (Enum)
- **TEXT_EXTRACTION**: Standard text extraction from PDF
- **OCR**: Optical character recognition applied
- **HYBRID**: Combination of text extraction and OCR
- **IMAGE_ANALYSIS**: Existing image processing method

### Document (Enhanced)
- **processing_method**: ProcessingMethod enum
- **ocr_applied**: Boolean flag
- **ocr_pages**: List of page numbers where OCR was used
- **ocr_confidence**: Average confidence score (0.0-1.0) if available

### OCRResult
- **page_number**: Integer
- **extracted_text**: String
- **confidence**: Float (0.0-1.0)
- **processing_time**: Float (seconds)
- **language**: String (detected or specified)

---

## Assumptions

1. **OCR Library**: Tesseract OCR is available and properly installed on deployment environment
2. **Image Quality**: Scanned PDFs have minimum 150 DPI resolution for acceptable OCR results
3. **Language Support**: Initial implementation focuses on English text; multilingual support can be added via configuration
4. **File Format**: PDFs are valid and not corrupted; validation happens before OCR attempt
5. **Resource Availability**: System has sufficient CPU and memory for concurrent OCR operations (minimum 2GB RAM per OCR process)
6. **Processing Context**: OCR processing occurs server-side; no client-side processing required
7. **Text Detection**: Threshold of 100 characters reasonably distinguishes between empty and content-bearing pages
8. **Page-Level Processing**: OCR operates on individual PDF pages converted to images, not entire documents at once

---

## Dependencies

### Internal Dependencies
- Existing PDF processor (`src/processors/pdf_processor.py`)
- Document model (`src/models/document.py`)
- Processing method enumeration
- Configuration system (`src/config/settings.py`)
- Async task tracking system

### External Dependencies
- **Tesseract OCR**: Open-source OCR engine (v4.0+)
- **pytesseract**: Python wrapper for Tesseract (v0.3.10+)
- **pdf2image**: Library to convert PDF pages to images (v1.16+)
- **Pillow (PIL)**: Image processing library (already in requirements)
- **poppler-utils**: PDF rendering utilities (system dependency)

---

## Out of Scope

### Explicitly Excluded

1. **OCR for Non-PDF Formats**: Image files (JPEG, PNG) continue using existing image processor
2. **Handwriting Recognition**: OCR limited to machine-printed text
3. **Real-Time OCR**: No live camera feed or real-time document scanning
4. **OCR Training/Customization**: No custom OCR model training or language model tuning
5. **Document Preprocessing**: No automatic image enhancement (denoising, deskewing, contrast adjustment)
6. **Format Conversion**: No conversion of scanned PDFs to searchable PDFs (output remains in knowledge base format)
7. **Cloud OCR Services**: No integration with Azure Computer Vision, AWS Textract, or Google Cloud Vision
8. **Form Recognition**: No structured data extraction from forms or tables
9. **Character-Level Editing**: No post-OCR text correction or spell-checking

---

## Open Questions

[NEEDS CLARIFICATION: OCR Accuracy Handling]
**Context**: When OCR produces low-confidence results or garbled text, system behavior needs definition.

**What we need to know**: How should the system handle low-confidence OCR results?

**Suggested Answers**:

| Option | Answer | Implications |
|--------|--------|--------------|
| A | Accept all OCR results regardless of confidence | Simpler implementation, may include some garbled text, users responsible for verifying accuracy |
| B | Reject pages below 70% confidence threshold | Higher quality results, risk of missing content on poor-quality scans, requires confidence scoring |
| C | Flag low-confidence results in metadata, include all text | Best user experience, allows users to make decisions, requires additional metadata fields |
| Custom | Provide your own answer | Explain alternative approach for handling OCR confidence |

**Your choice**: _[Wait for user response]_

---

[NEEDS CLARIFICATION: OCR Processing Mode]
**Context**: Large scanned PDFs may take several minutes to process. User experience during this time needs definition.

**What we need to know**: Should OCR always be asynchronous, or only for large documents?

**Suggested Answers**:

| Option | Answer | Implications |
|--------|--------|--------------|
| A | Always asynchronous (all OCR operations) | Consistent user experience, requires task tracking for all OCR, users always use task-status to check |
| B | Synchronous for <10 pages, async for larger | Simple documents process immediately, complex logic to switch modes, threshold configuration needed |
| C | User-controlled via force_async parameter | Maximum flexibility, more complex API, requires user understanding of trade-offs |
| Custom | Provide your own answer | Explain alternative approach for OCR processing modes |

**Your choice**: _[Wait for user response]_

---

[NEEDS CLARIFICATION: Temporary File Cleanup]
**Context**: OCR processing creates temporary image files from PDF pages. These files need proper lifecycle management.

**What we need to know**: When should temporary OCR image files be cleaned up?

**Suggested Answers**:

| Option | Answer | Implications |
|--------|--------|--------------|
| A | Immediately after each page is processed | Minimal disk usage, no caching benefits, higher I/O for retry operations |
| B | After entire document completes | Allows retry without regenerating images, requires more disk space, cleanup on process crash needed |
| C | Scheduled cleanup (every hour) | Supports debugging, highest disk usage, risk of orphaned files, requires background job |
| Custom | Provide your own answer | Explain alternative cleanup strategy |

**Your choice**: _[Wait for user response]_

---

## Related Features

- 001-mcp-knowledge-server: Core knowledge MCP server implementation
- Future: Document preprocessing pipeline enhancement
- Future: Cloud OCR service integration option

---

## Notes

### Testing Recommendations

1. **Test Documents Needed**:
   - Medical records PDF (scan-only, ~20 pages)
   - Financial services document (native text)
   - Mixed content PDF (native + scanned pages)
   - Low-quality scan (150 DPI)
   - High-quality scan (600 DPI)
   - Multi-column document
   - Document with tables and figures

2. **Performance Benchmarks**:
   - Baseline: Standard text extraction time
   - OCR overhead: Per-page processing time
   - Memory usage during concurrent operations
   - Async task status update latency

3. **Quality Verification**:
   - Manual review of OCR accuracy on sample documents
   - Comparison with commercial OCR tools (Adobe Acrobat, ABBYY)
   - Edge case handling (rotated pages, mixed orientations)

### Implementation Considerations

1. **Resource Management**: Implement connection pooling or process limits for Tesseract instances
2. **Progress Reporting**: Consider websocket connections for real-time progress updates
3. **Caching**: Consider caching OCR results keyed by PDF hash to avoid reprocessing
4. **Monitoring**: Add metrics for OCR success rate, average processing time, error frequency
5. **Graceful Degradation**: Ensure system remains functional if Tesseract installation is missing

---

## Acceptance Checklist

- [ ] User can upload scan-only PDF and retrieve searchable text
- [ ] System automatically detects need for OCR without user intervention
- [ ] Processing method is visible in document metadata and API responses
- [ ] Mixed-mode PDFs correctly combine extracted and OCR'd text
- [ ] Async OCR operations provide task ID and status tracking
- [ ] Configuration allows enabling/disabling OCR feature
- [ ] OCR processing completes within performance requirements
- [ ] Error handling prevents system crashes on corrupted PDFs
- [ ] Temporary files are properly cleaned up after OCR processing
- [ ] Unit and integration tests achieve >90% code coverage for OCR features
- [ ] Documentation updated with OCR configuration options and behavior
