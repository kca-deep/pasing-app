# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Next.js + FastAPI document parsing application that converts PDF/Office documents to Markdown/HTML/JSON. Supports multiple parsing strategies: Docling (default), Camelot (table extraction), MinerU (universal PDF parser), Dolphin (remote AI-powered OCR), and Remote OCR services.

**Tech Stack:**
- Frontend: Next.js 15.5.4 (App Router), React 19, Tailwind 4, shadcn/ui
- Backend: FastAPI, SQLAlchemy, Docling, Camelot, MinerU, PyTorch
- Database: SQLite (parsing_app.db at project root)

## Development Commands

### Starting the Development Servers

**Windows (Recommended):**
```powershell
.\start-dev.ps1
```
This script starts both backend (port 8000) and frontend (port 3000) in separate PowerShell windows.

**Manual Start:**
```bash
# Backend (from /backend)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info

# Frontend (from root)
npm run dev
```

### Testing

No test suite currently configured. Test manually via:
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Backend health: http://localhost:8000/

### Build Commands

```bash
# Frontend build
npm run build

# Frontend production start
npm start

# Linting
npm run lint
```

## Architecture

### Directory Structure

```
parsing-app/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Home page (recent parses)
│   └── parse/page.tsx     # Document parsing UI
├── components/            # React components
│   ├── upload/           # File upload & parsing options
│   └── viewer/           # Result viewer & metadata panel
├── lib/                   # Frontend utilities
│   ├── api.ts            # FastAPI client
│   └── types.ts          # TypeScript type definitions
├── backend/              # FastAPI backend
│   └── app/
│       ├── main.py       # FastAPI app & router registration
│       ├── config.py     # Configuration & paths
│       ├── models.py     # Pydantic models (requests/responses)
│       ├── database.py   # SQLAlchemy setup
│       ├── crud.py       # Database operations
│       ├── schemas.py    # SQLAlchemy ORM models
│       ├── api/          # API route handlers
│       │   ├── parsing.py        # Main /parse endpoint
│       │   ├── async_parsing.py  # Async /parse/async endpoint
│       │   ├── results.py        # /result & /parsed-documents
│       │   ├── documents.py      # /documents & /upload
│       │   └── health.py         # / health check
│       └── services/     # Parsing engines
│           ├── docling.py            # Docling parser
│           ├── mineru_parser.py      # MinerU parser
│           ├── dolphin_remote.py     # Dolphin remote GPU parser
│           ├── remote_ocr_parser.py  # Remote OCR parser
│           └── tables.py             # Camelot integration
├── docu/                 # Input documents (uploaded files)
├── output/               # Parsed results (organized by document name)
└── parsing_app.db        # SQLite database (Document records)
```

### Parsing Strategy Flow

The backend supports **5 parsing strategies** selected via `TableParsingOptions`:

1. **Remote OCR** (`use_remote_ocr=True`) **[Dedicated Parser]**
   - External OCR service: http://kca-ai.kro.kr:8005/ocr/extract
   - Engines:
     * `tesseract` - Fast (~0.2s)
     * `paddleocr` - Accurate (~1.6s) ⭐ Recommended
     * `dolphin` - AI-powered (~5s)
   - Best for: Korean scanned documents/images
   - Handler: `backend/app/services/remote_ocr_parser.py`
   - **Note:** Uses dedicated parser, NOT Docling (Docling doesn't support remote OCR)

2. **Dolphin Remote** (`use_dolphin=True`) **[Remote GPU Only]**
   - ByteDance Dolphin 1.5 multimodal AI running on remote GPU server
   - High accuracy for abbreviations, brackets, dates (83.21 on OmniDocBench)
   - Handler: `backend/app/services/dolphin_remote.py`
   - Options: `dolphin_parsing_level` (page/element/layout), `dolphin_max_batch_size`
   - **Note:** No local Dolphin installation - all inference done on remote server

3. **MinerU** (`use_mineru=True`)
   - Universal PDF parser with multilingual OCR (84 languages)
   - Auto-detects document structure (merged cells, hierarchical tables)
   - Handler: `backend/app/services/mineru_parser.py`
   - Options: `mineru_lang` (auto/ko/zh/en/ja), `mineru_use_ocr`

4. **Camelot** (`use_camelot=True`)
   - PDF-only table extraction (lattice/stream/hybrid modes)
   - Replaces Docling tables in final output
   - Handler: `backend/app/table_utils.py` → `backend/app/services/tables.py`
   - Options: `camelot_mode`, `camelot_accuracy_threshold`, `camelot_pages`

5. **Docling** (default)
   - General-purpose document parser (PDF/DOCX/PPTX/HTML)
   - Handler: `backend/app/services/docling.py`
   - Options: OCR (`do_ocr`, `ocr_lang`), Picture Description (`do_picture_description`)
   - **OCR Engine:** EasyOCR only (local). Does NOT support remote OCR server

**Selection Logic** (in `backend/app/api/parsing.py`):
```python
if opts.use_remote_ocr:        # Remote OCR
elif opts.use_dolphin:         # Dolphin (remote GPU)
elif opts.use_mineru:          # MinerU
elif opts.use_camelot:         # Docling + Camelot hybrid
else:                          # Docling only
```

### Key Data Flow

1. **Upload:** Frontend → `POST /upload` → saves to `/docu`
2. **Parse:** Frontend → `POST /parse` → parsing strategy execution → saves to `/output/{doc_name}/`
3. **Results:** Frontend → `GET /result/{filename}` → returns cached result
4. **Database:** All parses tracked in `parsing_app.db` (Document model)

### Frontend State Management

- No global state library (React hooks only)
- API calls via `lib/api.ts` (uses native `fetch`)
- File uploads use `FormData` with 5-minute timeout
- Async parsing uses polling via `GET /parse/status/{job_id}`

### Backend Parsing Metadata

All parsing responses include `ParsingMetadata`:
- `parser_used`: "docling" | "mineru" | "dolphin" | "camelot" | "remote-ocr"
- `table_parser`: "docling" | "camelot" | "mineru" (when tables extracted)
- `ocr_enabled`: bool
- `ocr_engine`: "easyocr" | "remote-tesseract" | "remote-paddleocr" | "remote-dolphin"
- Parser-specific fields: `camelot_mode`, `dolphin_parsing_level`, `mineru_lang`

## Important Patterns

### Error Handling

**Backend:**
- Use `HTTPException(status_code, detail)` for client errors
- Log errors with `logger.error(msg, exc_info=True)` for tracebacks
- Return warnings via `ParseResponse.warnings` (list of strings)
- Check parser availability via `check_*_installation()` functions (e.g., `check_mineru_installation()`)

**Frontend:**
- API errors thrown as `Error` objects with `response.json().detail || response.statusText`
- Display errors in UI via state: `setError(err.message)`

### Adding New Parsing Options

1. **Backend:** Update `TableParsingOptions` in `backend/app/models.py`
2. **Frontend:** Update `ParseOptions` interface in `lib/types.ts`
3. **UI:** Add controls in `components/upload/ParsingOptions.tsx`
4. **Parser:** Implement logic in `backend/app/api/parsing.py` or new service file

### Database Operations

- Use `app.database.get_db()` dependency for sessions
- CRUD functions in `app/crud.py` (e.g., `get_document_by_filename`, `create_document`)
- ORM models in `app/schemas.py` (e.g., `Document`)
- Always use `try/except` for DB operations (non-blocking on errors)

### Output Structure

Parsed documents saved to `output/{doc_name}/`:
```
output/sample/
├── sample.md              # Main content
├── tables/               # Extracted tables (CSV/JSON)
└── pictures/             # Image descriptions (JSON)
```

## Environment Variables

**Backend (.env in /backend):**

All backend environment variables are optional with sensible defaults. Copy `backend/.env.example` to `backend/.env` and customize as needed.

### API Server Settings
- `API_HOST`: Server host address (default: `0.0.0.0`)
- `API_PORT`: Server port (default: `8000`)
- `LOG_LEVEL`: Logging level - DEBUG/INFO/WARNING/ERROR (default: `INFO`)

### CORS Configuration
- `CORS_ALLOW_ORIGINS`: Allowed origins, comma-separated (default: `*`)
  - **Production:** Set to specific domains (e.g., `http://localhost:3000,https://yourdomain.com`)
- `CORS_ALLOW_CREDENTIALS`: Allow credentials (default: `True`)
- `CORS_ALLOW_METHODS`: Allowed HTTP methods (default: `*`)
- `CORS_ALLOW_HEADERS`: Allowed headers (default: `*`)

### Database Configuration
- `DATABASE_ECHO`: Log SQL queries - True/False (default: `True`)
  - **Production:** Set to `False` for better performance
- `DATABASE_PATH`: Database file path relative to backend/ (default: `../parsing_app.db`)

### Remote Service URLs
- `DOLPHIN_GPU_SERVER`: Dolphin GPU server URL (default: `http://kca-ai.kro.kr:8005`)
- `REMOTE_OCR_SERVER`: Remote OCR server URL (default: `http://kca-ai.kro.kr:8005`)

### Timeout Settings (seconds)
- `REMOTE_OCR_HEALTH_TIMEOUT`: Remote OCR health check timeout (default: `5`)
- `REMOTE_OCR_REQUEST_TIMEOUT`: Remote OCR request timeout (default: `30`)
- `DOLPHIN_HEALTH_TIMEOUT`: Dolphin GPU health check timeout (default: `5`)
- `DOLPHIN_INFERENCE_TIMEOUT`: Dolphin inference timeout (default: `60`)

### OCR Default Settings
- `DEFAULT_OCR_LANGUAGES`: Remote OCR default languages, comma-separated (default: `eng,kor`)
- `DEFAULT_DOCLING_OCR_LANGUAGES`: Docling EasyOCR languages, comma-separated (default: `ko,en`)

### PDF Processing Settings
- `PDF_RENDER_DPI`: PDF to image DPI for OCR (default: `300`)
  - Higher values improve OCR accuracy but increase processing time
- `DOLPHIN_IMAGE_TARGET_SIZE`: Dolphin image target size in pixels (default: `896`)

### GPU Server Settings (for gpu_server.py)
- `GPU_SERVER_HOST`: GPU server host (default: `0.0.0.0`)
- `GPU_SERVER_PORT`: GPU server port (default: `8001`)
- `GPU_SERVER_LOG_LEVEL`: GPU server log level (default: `info`)
- `DOLPHIN_MAX_LENGTH`: Dolphin max generation tokens (default: `4096`)
- `DOLPHIN_TEMPERATURE`: Dolphin sampling temperature (default: `0.0`)
- `DOLPHIN_USE_FP16`: Use FP16 on GPU - True/False (default: `True`)

**Frontend (.env.local in root):**
- `NEXT_PUBLIC_API_URL`: Backend URL (default: `http://localhost:8000`)

## Dependencies

### Backend Critical Dependencies

- `docling>=2.57.0`: Core document parsing
- `camelot-py==1.0.9`: PDF table extraction (requires `ghostscript` binary)
- `mineru>=2.5.4`: Universal PDF parser (optional)
- `transformers>=4.40.0`: For Dolphin/VLM models
- `torch>=2.9.0`: Deep learning backend
- `fastapi==0.115.0`, `uvicorn==0.32.0`: Web framework
- `sqlalchemy==2.0.36`: ORM

**Note:** MinerU and Dolphin are optional. Check availability via:
```python
from app.services.mineru_parser import MINERU_AVAILABLE
from app.services.dolphin_remote import DOLPHIN_REMOTE_AVAILABLE
```

### Frontend Critical Dependencies

- `next==15.5.4`: App Router framework
- `react-markdown`, `remark-gfm`, `rehype-raw`: Markdown rendering
- `@radix-ui/*`: UI primitives (used by shadcn/ui)

## Testing Strategy

**Manual Testing Workflow:**
1. Start dev servers via `start-dev.ps1`
2. Upload test document via frontend: http://localhost:3000/parse
3. Select parsing options (strategy, OCR, table extraction)
4. Verify output in `output/{doc_name}/` folder
5. Check API logs in backend terminal window

**Testing Different Parsers:**
- Remote OCR: Enable "Remote OCR" toggle, select engine (tesseract/paddleocr/dolphin)
- Dolphin: Select "Dolphin (AI-Powered)" strategy, adjust parsing level
- MinerU: Select "MinerU (Universal)" strategy, set language
- Camelot: Select "Camelot (Tables)" strategy, choose mode (lattice/stream/hybrid)
- Docling: Default strategy (no special selection needed)

## Common Issues

### Backend Won't Start

- Check Python version (requires 3.9+)
- Verify `backend/requirements.txt` installed: `pip install -r backend/requirements.txt`
- Ensure `docu/` and `output/` folders exist (auto-created in `config.py`)

### MinerU/Dolphin Not Available

- MinerU is optional - check `MINERU_AVAILABLE` flag in code
- Dolphin requires remote GPU server access - check `DOLPHIN_REMOTE_AVAILABLE`
- Application degrades gracefully (uses Docling as fallback)

### Camelot Import Errors

- Requires `ghostscript` binary installed on system (not Python package)
- Windows: Install via Chocolatey or official installer
- Check `CAMELOT_AVAILABLE` flag (auto-detected)

### Database Locked Errors

- SQLite `check_same_thread=False` already configured in `database.py`
- If persists, delete `parsing_app.db` and restart (database auto-recreates)

## Code Style

- Backend: Follow PEP 8, use type hints where possible
- Frontend: TypeScript strict mode, functional components only
- Use existing logger instances (`logger = logging.getLogger(__name__)`)
- Prefix log messages with emoji for visibility (e.g., `logger.info("📄 Parsing started")`)

## Remote GPU Server (Dolphin)

The GPU server is a **standalone FastAPI server** designed to run on a remote GPU machine.

### Architecture:
- **GPU Server:** `backend/gpu_server.py` - Runs Dolphin model inference on GPU
- **Client:** `backend/app/services/dolphin_remote.py` - Calls GPU server via HTTP
- **Default Server:** `http://kca-ai.kro.kr:8005` (Unified OCR Server)

### Setup (GPU Server Machine):

See `backend/GPU_SERVER.md` for detailed setup instructions.

**Quick Start:**
```bash
# Copy backend/gpu_server.py to your GPU server
cd /path/to/gpu-server
pip install fastapi uvicorn transformers torch pillow

# Download Dolphin model
pip install huggingface-hub
huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./dolphin_models/Dolphin-1.5

# Run GPU server
python gpu_server.py --model-path ./dolphin_models/Dolphin-1.5 --port 8001
```

### Environment Variable (Backend):
```bash
# backend/.env
DOLPHIN_GPU_SERVER=http://kca-ai.kro.kr:8005  # Unified OCR Server (default)
# Or use your own GPU server:
# DOLPHIN_GPU_SERVER=http://192.168.1.100:8001
```

The backend automatically checks GPU server availability on startup. If unavailable, Dolphin parsing is disabled (graceful degradation).

## Dolphin Integration Status

**Current Phase:** Phase 5 (Testing) - Core implementation complete
- **Architecture:** Remote GPU only (no local installation)
- See `prompts/dolphin-integration-plan.md` for detailed integration plan
- Implementation files: `backend/app/services/dolphin_remote.py`, `backend/app/services/dolphin_utils.py`
- Frontend UI complete: `components/upload/ParsingOptions.tsx` has Dolphin strategy selector
- **Remaining:** E2E testing and accuracy benchmarking vs MinerU

**Important:** Local Dolphin parser (`dolphin_parser.py`) has been removed. Only remote GPU server is used.
