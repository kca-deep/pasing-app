# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack document parsing application that converts PDF, DOCX, PPTX, and HTML files into Markdown/HTML/JSON formats with high accuracy. The system uses a hybrid parsing strategy combining multiple engines (Docling, Camelot, MinerU, Dolphin Remote GPU, Remote OCR) and includes integration with Dify Knowledge Base for RAG applications.

**Stack**: Next.js 15 (React 19) frontend + FastAPI backend + SQLite database

## Development Commands

### Starting Development Servers

**Recommended**: Use PowerShell script to start both servers simultaneously:
```powershell
.\start-dev.ps1
```
This starts:
- Backend (FastAPI): http://localhost:8000
- Frontend (Next.js): http://localhost:3000

**Manual start** (if needed):
```bash
# Backend only
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend only
npm run dev
```

**Stop servers**:
```powershell
.\stop-dev.ps1
```

### Backend Commands

```bash
# Create/activate virtual environment (first time setup)
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Database initialization
python -m app.init_db

# Run backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Commands

```bash
# Install dependencies
npm install

# Development server (with Turbopack)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Linting
npm run lint
```

## Architecture

### Backend Architecture (FastAPI)

**Entry Point**: `backend/app/main.py` - FastAPI application with CORS, database initialization on startup

**API Routers** (`backend/app/api/`):
- `parsing.py` - Main parsing endpoint (`/parse`), orchestrates all parsing strategies
- `async_parsing.py` - Background parsing jobs (`/parse/async`, `/parse/status/{job_id}`)
- `documents.py` - File upload and document management
- `results.py` - Retrieve parsed results
- `dify.py` - Dify Knowledge Base integration
- `database.py` - Database operations and queries
- `health.py` - Health check endpoint

**Parsing Strategy Selection** (`backend/app/api/parsing.py`):

The parsing logic follows a priority-based strategy selection:

1. **Remote OCR** (if `use_remote_ocr=True` and server available)
   - Best for: Korean/scanned documents, images
   - Uses external OCR server with multiple engines (Upstage, RapidOCR, PaddleOCR)
   - Returns Markdown only

2. **Dolphin Remote GPU** (if `use_dolphin=True` and server available)
   - Best for: AI-powered high-accuracy parsing
   - Requires GPU server connection (env: `DOLPHIN_GPU_SERVER`)
   - Parsing levels: fast/normal/detailed
   - Handles tables, images, formulas automatically

3. **MinerU** (if `use_mineru=True` and library installed)
   - Best for: Universal PDF parsing with good formula/table support
   - Local library (`magic-pdf` package)
   - Supports multiple output formats (Markdown/HTML)

4. **Docling + Camelot Hybrid** (default fallback)
   - Docling: Document structure and content extraction
   - Camelot (optional): High-accuracy table parsing for PDFs
   - Most flexible, works for all supported file types

**Key Services** (`backend/app/services/`):
- `docling.py` - Core Docling parsing with OCR/VLM options
- `dolphin_remote.py` - Dolphin Remote GPU integration
- `remote_ocr_parser.py` - Remote OCR service integration
- `mineru_parser.py` - MinerU library wrapper
- `tables.py` - Table integration and processing
- `pictures.py` - Image classification and VLM description filtering
- `dify_service.py` - Dify API client for Knowledge Base operations

**Utilities** (`backend/app/utils/`):
- `logging_utils.py` - Standardized logging utility with `ParserLogger` class

**Database** (`backend/app/`):
- `database.py` - SQLAlchemy session management
- `db_models.py` - ORM models (Document, Table, ParsingHistory, DifyUploadLog)
- `crud.py` - Database operations
- `schemas.py` - Pydantic schemas for API validation
- Database file: `parsing_app.db` (SQLite, in project root)

**Table Extraction** (`backend/app/table_utils.py`):
- Camelot-based extraction for PDFs (high accuracy)
- Docling-based extraction for all formats
- Complexity scoring to identify merged cells/complex tables
- JSON export with cell-level structure

**Configuration** (`backend/app/config.py`):
- `DOCU_FOLDER` - Input documents folder (project root/docu)
- `OUTPUT_FOLDER` - Parsed output folder (project root/output)
- CORS settings loaded from environment variables

### Logging Standards

All parsing strategies use standardized logging via the `ParserLogger` class for consistency, maintainability, and ease of debugging.

**Log Structure**:
```
🎯 [Parser Name] Parsing: filename.pdf
    📋 Config Key: value
    ⚙️ Step 1/4: Description...
        ├─ Sub-action: details
        └─ Result: outcome
    ✅ Complete: summary
        └─ Metric: value
```

**Standard Emojis**:

| Emoji | Purpose | Example |
|-------|---------|---------|
| 🎯 | Parser Start | `🎯 [Docling] Parsing: doc.pdf` |
| 📋 | Configuration | `📋 OCR Engine: easyocr` |
| 📄 | Document Processing | `📄 Converting PDF...` |
| 🔍 | Analysis/Detection | `🔍 Analyzing document...` |
| ⚙️ | Processing Step | `⚙️ Step 1/4: Creating dataset...` |
| 📖 | Page Processing | `📖 Processing Page 1/10` |
| 🌐 | Remote API Call | `🌐 Calling GPU server...` |
| 💾 | Saving Output | `💾 Saved to output/content.md` |
| 🔗 | Merging/Combining | `🔗 Merging all pages...` |
| ✅ | Success | `✅ Complete: 10 pages processed` |
| ⚠️ | Warning/Fallback | `⚠️ Fallback to local OCR` |
| ❌ | Error | `❌ Failed: Connection timeout` |

**Indentation Rules**:
- Level 0: Parser Start (no indent)
- Level 1: Configuration & Main Steps (4 spaces)
- Level 2: Sub-steps (8 spaces)
- Level 3: Details (12 spaces)

**Log Levels**:
- **DEBUG**: Detailed internal operations (development only)
- **INFO**: Normal processing steps and progress
- **WARNING**: Fallback methods, partial failures
- **ERROR**: Parsing failures, exceptions

**Usage Example**:
```python
from app.utils.logging_utils import ParserLogger

parser_logger = ParserLogger("Docling", logger)

# Start with configuration
parser_logger.start(filename, output_format="markdown", ocr_enabled=True)

# Log processing steps
parser_logger.step(1, 3, "Processing document...")
parser_logger.detail("Extracted 100 elements")

# Log completion with metrics
parser_logger.success("Parsing complete", pages=10, tables=5)

# Log errors
parser_logger.error("Parsing failed", exc_info=True, reason="Connection timeout")
```

**Key Methods**:
- `start(filename, **config)` - Log parser start with configuration
- `step(current, total, description)` - Log main processing step
- `sub_step(description, emoji=None)` - Log sub-step with optional emoji
- `detail(description, last=False)` - Log detail information
- `page(current, total)` - Log page processing
- `remote_call(endpoint, description=None)` - Log remote API call
- `success(summary, **metrics)` - Log successful completion
- `warning(message, **details)` - Log warning
- `error(summary, exc_info=False, **details)` - Log error

**Resource Checks** (module-level):
```python
from app.utils.logging_utils import log_resource_available, log_resource_unavailable

log_resource_available(logger, "Dolphin GPU Server", url="http://server:8005")
log_resource_unavailable(logger, "MinerU", reason="Not installed")
```

### Frontend Architecture (Next.js 15 App Router)

**Pages** (`app/`):
- `page.tsx` - Home page with parsed documents grid
- `parse/page.tsx` - Document upload and parsing interface
- `viewer/page.tsx` - Markdown/HTML content viewer
- `dify/page.tsx` - Dify Knowledge Base upload interface

**API Client** (`lib/api.ts`):
- All backend API calls centralized here
- Base URL: `process.env.NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`)
- Key functions: `uploadFile()`, `parseDocument()`, `parseDocumentAsync()`, `getParsingStatus()`, `uploadToDify()`

**UI Components** (`components/ui/`):
- Built with shadcn/ui and Radix UI primitives
- Styled with Tailwind CSS v4
- Key components: Card, Button, Badge, Progress, Dialog, Tabs

**Styling**:
- Tailwind CSS v4 with PostCSS
- Custom animations defined in `app/globals.css`
- Dark mode support with `next-themes`

### Output Folder Structure

Each parsed document creates a folder in `output/`:

```
output/
  {document_name}/
    content.md          # Main content file
    metadata.json       # Parsing metadata
    tables/             # Extracted tables (if enabled)
      table_001.json
      table_002.json
    images/             # Extracted images (MinerU/Dolphin only)
```

## Key Parsing Options

When calling `/parse` endpoint, key options in request body:

```json
{
  "filename": "document.pdf",
  "output_format": "markdown",  // markdown | html | json

  // Strategy selection (priority order: Remote OCR > Dolphin > MinerU > Docling+Camelot)
  "use_remote_ocr": false,      // Use external OCR server
  "use_dolphin": false,          // Use Dolphin Remote GPU
  "use_mineru": false,           // Use MinerU library
  "use_camelot": false,          // Use Camelot for table parsing (Docling+Camelot hybrid)

  // OCR options (for Docling)
  "do_ocr": false,               // Enable OCR
  "ocr_engine": "easyocr",       // easyocr | tesseract
  "ocr_lang": ["ko", "en"],      // OCR languages

  // Table parsing options
  "extract_tables": true,        // Extract tables to JSON files
  "table_mode": "accurate",      // fast | accurate
  "camelot_mode": "lattice",     // lattice | stream (for Camelot)

  // Image analysis options
  "do_picture_description": false,       // Enable VLM for all images
  "auto_image_analysis": false,          // Smart image filtering (text vs visualization)

  // Output options
  "save_to_output_folder": true  // Save to output/{doc_name}/ instead of docu/
}
```

## Important File Paths

**Frontend**:
- `/app/parse/page.tsx` - Main parsing UI with strategy selection
- `/app/viewer/page.tsx` - Content viewer with syntax highlighting
- `/lib/api.ts` - API client functions
- `/lib/types.ts` - TypeScript type definitions

**Backend**:
- `/backend/app/api/parsing.py` - Core parsing logic (lines 37-586)
- `/backend/app/services/docling.py` - Docling parser configuration
- `/backend/app/table_utils.py` - Table extraction functions
- `/backend/app/db_models.py` - Database schema definitions

**Data Folders**:
- `/docu/` - Input documents (upload destination)
- `/output/` - Parsed output with structured folders
- `/parsing_app.db` - SQLite database

## Database Schema

**Documents Table** (`Document` model):
- Stores metadata for all uploaded documents
- Tracks parsing status: pending | processing | completed | failed
- Links to tables and parsing history

**Tables Table** (`Table` model):
- One-to-many with Document
- Stores table metadata (rows, cols, complexity, caption)
- References JSON files in output folder

**ParsingHistory Table** (`ParsingHistory` model):
- Audit trail of all parsing attempts
- Stores parsing options, duration, error messages

**DifyUploadLog Table** (`DifyUploadLog` model):
- Tracks uploads to Dify Knowledge Base
- Stores dataset_id, document_id, batch_id, indexing status

## Remote Services Configuration

**Dolphin Remote GPU Server**:
- Environment variable: `DOLPHIN_GPU_SERVER` (default: `http://kca-ai.kro.kr:8005`)
- Availability checked at runtime in `backend/app/services/dolphin_remote.py`

**Remote OCR Server**:
- Environment variable: `REMOTE_OCR_SERVER` (default: `http://kca-ai.kro.kr:8005`)
- Supports multiple engines: upstage, rapidocr, paddleocr
- Language support: Korean (kor), English (eng), Japanese (jpn), Chinese (chi)

**Dify API**:
- Configuration stored in database (DifyConfig table)
- API key and base URL configured via `/dify` page
- Knowledge Base integration for RAG applications

## Testing Considerations

When writing tests:
- Backend: Use pytest, mock external services (Dolphin, Remote OCR servers)
- Database: Use in-memory SQLite for test isolation
- File operations: Mock file I/O or use temporary directories
- Parsing: Test with small sample documents in test fixtures
- API endpoints: Use FastAPI TestClient

## Common Development Tasks

**Adding a new parsing strategy**:
1. Create service file in `backend/app/services/`
2. Add availability check (similar to `CAMELOT_AVAILABLE`, `MINERU_AVAILABLE`)
   - Use `log_resource_available()` / `log_resource_unavailable()` for consistent logging
3. Implement parser function with standardized logging
   - Import: `from app.utils.logging_utils import ParserLogger`
   - Initialize: `parser_logger = ParserLogger("Your Parser", logger)`
   - Use `parser_logger.start()`, `step()`, `success()`, `error()` methods
4. Update `parsing.py` strategy selection logic
5. Add parsing metadata fields in `models.py:ParsingMetadata`
6. Update frontend UI in `app/parse/page.tsx` with new options

**Logging Best Practices**:
- Always use `ParserLogger` for consistent format across all parsers
- Log parser start with `start(filename, **config)` to show configuration
- Use `step(current, total, description)` for main processing steps (e.g., Step 1/4, Step 2/4)
- Use `success(summary, **metrics)` with meaningful metrics (pages, tables, duration, etc.)
- Use `error(summary, exc_info=True, **details)` for errors with context
- Follow the standard emoji and indentation guidelines (see Logging Standards section)

**Adding a new API endpoint**:
1. Create router in `backend/app/api/` or add to existing router
2. Define request/response schemas in `backend/app/schemas.py`
3. Import and register router in `backend/app/main.py`
4. Add client function in `lib/api.ts`
5. Update TypeScript types in `lib/types.ts`

**Database schema changes**:
1. Update ORM models in `backend/app/db_models.py`
2. Update Pydantic schemas in `backend/app/schemas.py`
3. Update CRUD operations in `backend/app/crud.py`
4. Consider migration strategy (currently using `init_db.py`)

## Environment Variables

**Backend** (`.env` or system environment):
- `LOG_LEVEL` - Logging level (default: INFO)
- `CORS_ALLOW_ORIGINS` - CORS origins (default: *)
- `DOLPHIN_GPU_SERVER` - Dolphin Remote GPU server URL
- `REMOTE_OCR_SERVER` - Remote OCR server URL
- `DEFAULT_DOCLING_OCR_LANGUAGES` - Default OCR languages (default: ko,en)

**Frontend** (`.env.local`):
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

## Known Limitations

- Dolphin Local mode has been removed; only Dolphin Remote GPU is supported
- Remote OCR returns Markdown only (no HTML/JSON)
- Camelot only works with PDF files (lattice/stream modes)
- VLM picture description requires significant processing time
- Large files (>100MB) may timeout; use async parsing endpoint instead
- MinerU installation requires `pip install magic-pdf[full]` (large dependency)
