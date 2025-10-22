# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a document parsing application consisting of:
- **Frontend**: Next.js 15 application with TypeScript and Tailwind CSS 4
- **Backend**: FastAPI service that uses Docling library directly for document parsing
- **Architecture**: Frontend communicates with FastAPI backend, which uses Docling Python library

The application parses documents (PDF, DOCX, PPTX, HTML) into Markdown format using IBM's Docling library directly.

### Implementation Plan

**Complete implementation roadmap** is available in `prompts/integrated-rag-parsing-implementation-plan.md` ⭐

This comprehensive plan includes:
- **Phase 1-5**: Core RAG parsing features (환경설정, 기본 파싱, 표 추출, 청킹, manifest 생성)
- **Phase 6-7**: CLI interface + AI table summaries
- **Phase 8-9**: RAG system integration + optimization
- **Phase 10**: Dify knowledge base auto-upload system

**When implementing features, follow the plan** for step-by-step guidance, detailed checklists, and validation methods.

## Tech Stack

### Frontend
- **Framework**: Next.js 15.5.4 with App Router
- **React**: 19.1.0
- **TypeScript**: 5.x with strict mode enabled
- **Styling**: Tailwind CSS 4 with PostCSS
- **UI Components**: shadcn/ui (New York style) with Lucide React icons
- **Build Tool**: Turbopack (Next.js native)
- **Testing**: Playwright 1.56.0

### Backend
- **Framework**: FastAPI 0.115.0
- **Server**: Uvicorn 0.32.0
- **Document Parser**: Docling + Camelot hybrid (high-accuracy table extraction)
  - **Text**: Docling (IBM's document parsing library)
  - **Tables**: Camelot (LATTICE + STREAM hybrid) for PDF files
  - **Pictures**: VLM Picture Description (SmolVLM, Granite Vision) - Optional
- **Environment**: Python 3.13 with virtual environment

## Development Commands

**IMPORTANT: All commands below are for Windows PowerShell**

### Frontend Commands (PowerShell)
```powershell
# Start Next.js development server (port 3000)
npm run dev

# Build production bundle
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

### Backend Commands (PowerShell)
```powershell
# Activate virtual environment
.\backend\venv\Scripts\Activate.ps1

# Start FastAPI development server (port 8000)
cd backend; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
cd backend; pip install -r requirements.txt

# Upload parsed documents to Dify knowledge base
cd backend; python app/upload_to_dify.py --manifest ../output/sample/manifest.json --content ../output/sample/content.md

# Set encoding for Unicode support (if needed)
$env:PYTHONIOENCODING="utf-8"
```

### Windows PowerShell Notes
- Use semicolon (`;`) for command chaining in PowerShell
- EasyOCR is required as a dependency for Docling's OCR functionality
- If PowerShell execution policy blocks scripts, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## Architecture

### Directory Structure

```
parsing-app/
├── app/                    # Next.js App Router (Frontend)
│   ├── page.tsx           # Main landing page
│   ├── layout.tsx         # Root layout with fonts
│   └── globals.css        # Global Tailwind styles
├── backend/               # Python FastAPI service
│   ├── app/
│   │   ├── main.py       # FastAPI application with endpoints
│   │   └── __init__.py
│   ├── venv/             # Python virtual environment
│   └── requirements.txt  # Python dependencies
├── docu/                  # Document storage folder
│   ├── README.md         # Document testing guide
│   ├── *.pdf             # Input PDFs for parsing
│   ├── *.docx            # Input Word documents
│   ├── *.html            # Input HTML files
│   └── *.md              # Output Markdown files (generated)
├── prompts/              # Implementation plans and guides ⭐
│   ├── docling-api-test-plan.md  # Complete test plan (Scenarios 1-10)
│   ├── fastapi-implementation-plan-scenario1-2.md  # Backend implementation guide
│   ├── integrated-rag-parsing-implementation-plan.md  # Complete RAG roadmap
│   └── picture-description-guide.md  # VLM Picture Description feature guide
├── components/            # React components (shadcn/ui)
├── lib/                   # Utility functions
│   └── utils.ts          # cn() helper for class merging
└── public/               # Static assets
```

### Service Architecture

**Two-tier architecture:**

1. **Frontend (Next.js)** - Port 3000
   - User interface for document selection and display
   - Currently displays default Next.js landing page
   - Will communicate with Backend API

2. **Backend (FastAPI)** - Port 8000
   - Exposes REST API endpoints at `backend/app/main.py`
   - Manages document files in `/docu` folder
   - **Hybrid parsing strategy** (automatic):
     - **PDF files**: Camelot (LATTICE + STREAM) for high-accuracy table extraction
     - **Other files** (DOCX, PPTX, HTML): Docling for all content
   - Supports OCR, table extraction, and structure preservation

### Backend API Endpoints

The FastAPI backend (`backend/app/main.py`) provides:

- `GET /` - API status check, returns version and parsing strategy
  - Shows: Camelot availability, default parsing strategy
- `GET /documents` - List all documents in `/docu` folder (returns `DocumentInfo[]`)
- `POST /parse` - Parse a document to Markdown/HTML/JSON
  - Request body: `ParseRequest` with filename and options
  - **PDF files**: Automatically uses Camelot hybrid (LATTICE + STREAM)
  - **Other files**: Automatically uses Docling
  - Options: `do_ocr`, `table_mode`, `camelot_mode`, `output_format`, `do_picture_description`, etc.
  - Returns: `ParseResponse` with content, stats, table summary, pictures summary, and saved file path
- `GET /download/{filename}` - Download converted file

**Key implementation details:**
- **Version**: 2.2.0
- CORS enabled for all origins (`backend/app/main.py`)
- Document folder path is `../docu` relative to backend
- Output folder: `../output/{document_name}/` structure
  - `content.md` - Main document with integrated tables
  - `tables/` - Extracted tables (JSON, CSV, Markdown)
- **Default strategy**: Docling + Camelot hybrid
  - Docling table parsing is automatically disabled for PDFs
  - Camelot tables are integrated into final content
- **Picture Description**: Optional VLM-based image analysis (v2.2.0+)
  - Disabled by default (requires VLM dependencies)
  - Supports SmolVLM, Granite Vision, and custom Hugging Face models
  - Automatically filters images by area threshold
- Supports multiple output formats: Markdown (default), HTML, JSON

### Path Aliases (Frontend)

TypeScript is configured with the following import aliases:
- `@/*` - Root directory alias for all imports

shadcn/ui components.json defines additional aliases:
- `@/components` - UI components
- `@/ui` - shadcn/ui components specifically
- `@/lib` - Utility functions
- `@/hooks` - React hooks
- `@/utils` - Points to `lib/utils`

### Styling System

- **Tailwind Configuration**: Uses Tailwind CSS 4 with the neutral base color and CSS variables enabled
- **Global Styles**: Located at `app/globals.css`
- **Component Styling**: Uses the `cn()` utility from `lib/utils.ts` to merge Tailwind classes with clsx and tailwind-merge
- **Fonts**: Uses Geist Sans and Geist Mono fonts loaded via `next/font/google` in the root layout

### shadcn/ui Configuration

The project is set up with shadcn/ui using:
- Style: "new-york"
- RSC (React Server Components): Enabled
- Icon library: Lucide React
- CSS variables: Enabled for theming

Add new shadcn/ui components with:
```bash
npx shadcn@latest add [component-name]
```

## Code Conventions

- **TypeScript**: Strict mode is enabled, all code should be fully typed
- **ESLint**: Uses Next.js recommended configurations (`next/core-web-vitals` and `next/typescript`)
- **Component Pattern**: Functional components with TypeScript types
- **Styling**: Prefer Tailwind utility classes; use the `cn()` helper for conditional classes

### 🎨 Styling and Theming Rules

**IMPORTANT: Never hardcode colors, spacing values, or design tokens**

All styling must reference the shadcn/ui theme system defined in `app/globals.css`. This ensures consistent theming, dark mode support, and maintainability.

#### Color Usage Rules

1. **Always use CSS variable classes for colors**
   - ✅ **Correct**: `className="bg-primary text-primary-foreground"`
   - ✅ **Correct**: `className="bg-secondary text-secondary-foreground"`
   - ✅ **Correct**: `className="bg-muted text-muted-foreground"`
   - ✅ **Correct**: `className="border-border bg-background"`
   - ❌ **Wrong**: `className="bg-blue-500 text-white"`
   - ❌ **Wrong**: `className="bg-gray-100 text-gray-900"`
   - ❌ **Wrong**: `style={{ backgroundColor: '#3b82f6' }}`

2. **Reference theme variables from `app/globals.css`**

   Available theme color tokens:
   - `background` / `foreground` - Base page colors
   - `primary` / `primary-foreground` - Primary actions and buttons
   - `secondary` / `secondary-foreground` - Secondary actions
   - `muted` / `muted-foreground` - Muted backgrounds and text
   - `accent` / `accent-foreground` - Accent elements
   - `destructive` / `destructive-foreground` - Error states
   - `card` / `card-foreground` - Card backgrounds
   - `popover` / `popover-foreground` - Popover backgrounds
   - `border` - Border colors
   - `input` - Input field borders
   - `ring` - Focus ring colors

3. **Use Tailwind's built-in spacing scale**
   - ✅ **Correct**: `className="p-4 mb-8 gap-6"`
   - ❌ **Wrong**: `style={{ padding: '16px', marginBottom: '32px' }}`

#### Examples

**Button Styling:**
```tsx
// ✅ Correct - Uses theme tokens
<Button className="bg-primary text-primary-foreground hover:bg-primary/90">
  Submit
</Button>

// ❌ Wrong - Hardcoded colors
<Button className="bg-blue-600 text-white hover:bg-blue-700">
  Submit
</Button>
```

**Card Styling:**
```tsx
// ✅ Correct - Uses theme tokens
<Card className="border-border bg-card">
  <CardHeader className="border-b border-border">
    <CardTitle className="text-card-foreground">Title</CardTitle>
  </CardHeader>
</Card>

// ❌ Wrong - Hardcoded colors
<Card className="border-gray-200 bg-white">
  <CardHeader className="border-b border-gray-100">
    <CardTitle className="text-gray-900">Title</CardTitle>
  </CardHeader>
</Card>
```

**Text Styling:**
```tsx
// ✅ Correct - Uses theme tokens
<p className="text-muted-foreground">Description text</p>
<h1 className="text-foreground">Main heading</h1>

// ❌ Wrong - Hardcoded colors
<p className="text-gray-600">Description text</p>
<h1 className="text-black">Main heading</h1>
```

### 🔧 MCP Tools - Mandatory Usage

**CRITICAL: Always use MCP tools when working with UI components and external libraries**

Failing to use MCP tools may result in outdated patterns, incorrect implementations, or inconsistent styling.

#### 1. shadcn/ui MCP - Required for ALL UI Changes

**Before creating or modifying any UI component**, you MUST:

1. **Search for existing components:**
   ```
   Use: mcp__shadcn__search_items_in_registries
   Purpose: Find if shadcn/ui already provides the component you need
   ```

2. **View component details:**
   ```
   Use: mcp__shadcn__view_items_in_registries
   Purpose: See the full implementation and available props
   ```

3. **Get usage examples:**
   ```
   Use: mcp__shadcn__get_item_examples_from_registries
   Purpose: See real-world usage patterns and best practices
   ```

**Examples:**

```
❌ WRONG: Manually creating a dialog component
✅ CORRECT: Search for "dialog" using shadcn MCP, then add with examples

❌ WRONG: Hardcoding a custom select dropdown
✅ CORRECT: Use mcp__shadcn__search_items_in_registries to find "select" component

❌ WRONG: Creating custom form inputs
✅ CORRECT: Use shadcn MCP to add "form" and "input" components
```

#### 2. Context7 MCP - Required for Library Documentation

**Before implementing features with external libraries**, you MUST:

1. **Resolve the library ID:**
   ```
   Use: mcp__context7__resolve-library-id
   Purpose: Get the correct Context7-compatible library identifier
   ```

2. **Fetch latest documentation:**
   ```
   Use: mcp__context7__get-library-docs
   Purpose: Get up-to-date API documentation and usage patterns
   ```

**When to use Context7 MCP:**
- Working with Next.js App Router features
- Using React 19 features (Server Components, Actions, etc.)
- Implementing FastAPI endpoints or middleware
- Integrating Docling parsing features
- Using react-markdown or other rendering libraries
- Any time you're unsure about API usage

**Examples:**

```
❌ WRONG: Implementing Next.js routing based on memory/assumptions
✅ CORRECT: Use context7 MCP to get latest Next.js 15 App Router docs

❌ WRONG: Guessing FastAPI async patterns
✅ CORRECT: Use context7 MCP to fetch FastAPI documentation for async/await

❌ WRONG: Using outdated react-markdown syntax
✅ CORRECT: Use context7 MCP to get latest react-markdown API reference
```

#### Mandatory Workflow for UI Development

**Step-by-step process:**

1. **Plan** → Understand requirements
2. **Search shadcn MCP** → Check if component exists
3. **Get Context7 docs** → Verify latest library APIs (if using external libs)
4. **Implement** → Use theme variables, never hardcode
5. **Verify** → Ensure proper theme usage and component patterns

**Example workflow for adding a data table:**

```
1. Search: mcp__shadcn__search_items_in_registries(query: "table")
2. View: mcp__shadcn__view_items_in_registries(items: ["@shadcn/table"])
3. Examples: mcp__shadcn__get_item_examples_from_registries(query: "table-demo")
4. Docs (if needed): context7 resolve "tanstack/table" → get library docs
5. Implement using discovered patterns with theme variables
```

## Configuration Files

- `next.config.ts` - Next.js configuration (currently using defaults)
- `tsconfig.json` - TypeScript compiler options with strict mode and path aliases
- `eslint.config.mjs` - ESLint configuration with Next.js presets
- `components.json` - shadcn/ui configuration and component registry
- `postcss.config.mjs` - PostCSS configuration for Tailwind CSS 4

## Development Workflow

### Starting the Full Stack (PowerShell)

To run the complete application, start both services:

1. **Start Backend API** (Terminal 1 - PowerShell):
   ```powershell
   cd backend; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Runs on port 8000
   - Auto-reloads on code changes
   - Uses Docling library directly (no separate service needed)
   - May take time on first document parse (downloads models on first run)

2. **Start Frontend** (Terminal 2 - PowerShell):
   ```powershell
   npm run dev
   ```
   - Runs on port 3000
   - Visit http://localhost:3000

### Testing the API (PowerShell)

Test endpoints using curl or Invoke-RestMethod in PowerShell:

```powershell
# Check API status
curl http://localhost:8000/
# or
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get

# List documents
Invoke-RestMethod -Uri "http://localhost:8000/documents" -Method Get

# Parse a PDF document (Camelot automatically used)
$body = @{
    filename = "sample.pdf"
    options = @{
        extract_tables = $true
        save_to_output_folder = $true
        output_format = "markdown"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/parse" -Method Post -ContentType "application/json" -Body $body

# Or simplest form (uses all defaults)
$body = @{ filename = "sample.pdf" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/parse" -Method Post -ContentType "application/json" -Body $body

# Parse with Picture Description (requires VLM dependencies)
$body = @{
    filename = "sample.pdf"
    options = @{
        do_picture_description = $true
        picture_description_model = "smolvlm"  # or "granite"
        save_to_output_folder = $true
    }
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/parse" -Method Post -ContentType "application/json" -Body $body
```

## Development Notes

- The development and build commands use Turbopack (`--turbopack` flag) for faster builds
- React Server Components (RSC) are enabled by default in the App Router
- The target ES version is ES2017
- Playwright is available for end-to-end testing
- Frontend is currently showing default Next.js page - needs UI implementation
- Backend environment variables can be configured via `.env` file in `backend/` directory

## Common Issues

### Backend Issues
- **Camelot not installed**: Run `pip install camelot-py[cv]` in the backend venv
- **EasyOCR not installed**: Run `pip install easyocr` in the backend venv
- **Model download on first run**: First document parse may take time as Docling downloads models
- **Camelot unavailable**: Check API status endpoint (`GET /`) to verify Camelot is available
  - If `camelot: false`, system will automatically fall back to Docling for PDFs
- **CORS errors**: Verify `allow_origins` setting in `backend/app/main.py`
- **File not found**: Ensure documents are placed in `/docu` folder
- **Memory issues with large files**: Consider processing specific pages with `camelot_pages` option
- **Unicode encoding errors on Windows**: Set `PYTHONIOENCODING=utf-8` before starting backend
- **No tables found**: Try different `camelot_mode` values: "hybrid" (default), "lattice", "stream"
- **Picture Description not working**: Install VLM dependencies with `pip install docling[vlm]`
  - See `prompts/picture-description-guide.md` for detailed setup instructions
  - Test with: `cd backend; .\test_picture_description.ps1`

## MCP Tools Usage Guide

This project has access to several MCP (Model Context Protocol) tools that should be used actively during development:

### Available MCP Tools

1. **Sequential Thinking (`mcp__sequential-thinking__sequentialthinking`)**
   - Use for complex problem-solving and multi-step tasks
   - Helps break down problems into manageable steps
   - Useful for planning implementation before coding
   - **When to use**:
     - Planning new features or refactoring
     - Debugging complex issues
     - Designing architecture changes

2. **Context7 (`mcp__context7__resolve-library-id`, `mcp__context7__get-library-docs`)**
   - Retrieves up-to-date documentation for libraries
   - **When to use**:
     - Learning new FastAPI features
     - Understanding Docling API parameters
     - Checking Next.js 15 App Router patterns
   - **Example**: Get latest FastAPI docs for async operations

3. **shadcn/ui MCP Tools**
   - `mcp__shadcn__search_items_in_registries` - Find components
   - `mcp__shadcn__view_items_in_registries` - View component details
   - `mcp__shadcn__get_item_examples_from_registries` - Get usage examples
   - **When to use**: Adding UI components to the Next.js frontend

4. **Playwright MCP Tools**
   - Browser automation for testing
   - **When to use**: E2E testing of the complete document parsing flow

### Best Practices for MCP Usage

1. **Use Sequential Thinking for Planning**
   ```
   Before implementing a new feature:
   - Use sequential thinking to break down the task
   - Identify dependencies and potential issues
   - Create a step-by-step implementation plan
   ```

2. **Use Context7 for Documentation**
   ```
   When working with libraries:
   - Resolve library ID first
   - Fetch relevant documentation
   - Apply latest best practices from docs
   ```

3. **Use shadcn/ui Tools for Frontend**
   ```
   When building UI:
   - Search for components matching requirements
   - View examples before implementing
   - Follow patterns from official examples
   ```

### Example MCP Workflow

**Scenario**: Implementing a new file upload feature

1. **Plan with Sequential Thinking**
   - Break down: UI component → API endpoint → Docling integration → Response handling
   - Identify: File validation, size limits, error handling

2. **Get Documentation with Context7**
   - FastAPI file upload best practices
   - Docling API file handling parameters

3. **Build UI with shadcn/ui**
   - Search for "file upload" or "dropzone" components
   - Get examples and implement with proper styling

4. **Test with Playwright** (optional)
   - Automate file upload testing
   - Verify parsing results in browser
