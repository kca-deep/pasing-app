"""
Parsed results endpoints.

Handles listing and retrieving previously parsed documents.
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import logging

from app.config import OUTPUT_FOLDER
from app.models import ParseResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/parsed-documents")
async def list_parsed_documents():
    """List all parsed documents in the output folder"""
    try:
        parsed_docs = []

        # Scan output folder for parsed documents
        if OUTPUT_FOLDER.exists():
            for doc_dir in OUTPUT_FOLDER.iterdir():
                if doc_dir.is_dir():
                    content_file = doc_dir / "content.md"
                    if content_file.exists():
                        # Get file stats
                        stat = content_file.stat()

                        # Read first few lines for preview
                        with open(content_file, 'r', encoding='utf-8') as f:
                            content = f.read(500)  # Read first 500 chars
                            preview = content[:200] + "..." if len(content) > 200 else content

                        # Check for tables
                        tables_dir = doc_dir / "tables"
                        table_count = 0
                        if tables_dir.exists():
                            table_count = len(list(tables_dir.glob("table_*.json")))

                        parsed_docs.append({
                            "document_name": doc_dir.name,
                            "parsed_at": stat.st_mtime,
                            "size_kb": round(stat.st_size / 1024, 2),
                            "preview": preview,
                            "table_count": table_count,
                            "output_dir": str(doc_dir)
                        })

        # Sort by parsed time (most recent first)
        parsed_docs.sort(key=lambda x: x["parsed_at"], reverse=True)

        return {
            "total": len(parsed_docs),
            "documents": parsed_docs
        }

    except Exception as e:
        logger.error(f"Error listing parsed documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{filename}")
async def get_parse_result(filename: str):
    """Get parsing result for a previously parsed document"""
    try:
        # Remove extension from filename to get document name
        # Only remove extension if it's a known document type
        file_path = Path(filename)
        known_extensions = {'.pdf', '.docx', '.pptx', '.html', '.txt', '.md'}

        if file_path.suffix.lower() in known_extensions:
            doc_name = file_path.stem
        else:
            # No known extension, use the full filename
            doc_name = filename

        # Check output folder
        doc_output_dir = OUTPUT_FOLDER / doc_name
        content_file = doc_output_dir / "content.md"

        if not content_file.exists():
            raise HTTPException(status_code=404, detail=f"Parsed result not found for {filename}")

        # Read content
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Calculate statistics
        lines = content.count('\n') + 1
        words = len(content.split())
        chars = len(content)

        # Check for table summary (if exists)
        table_summary = None
        tables_dir = doc_output_dir / "tables"
        if tables_dir.exists():
            json_tables = list(tables_dir.glob("table_*.json"))
            csv_tables = list(tables_dir.glob("table_*.csv"))
            md_tables = list(tables_dir.glob("table_*.md"))

            table_summary = {
                "total_tables": len(json_tables),
                "json_tables": len(json_tables),
                "csv_tables": len(csv_tables),
                "markdown_tables": len(md_tables),
                "json_table_ids": [f.stem for f in json_tables]
            }

        # Build output structure
        output_structure = {
            "output_dir": str(doc_output_dir),
            "content_file": str(content_file),
            "tables_dir": str(tables_dir) if tables_dir.exists() else None
        }

        return ParseResponse(
            success=True,
            filename=filename,
            markdown=content,
            stats={
                "lines": lines,
                "words": words,
                "characters": chars,
                "size_kb": round(chars / 1024, 2)
            },
            saved_to=str(content_file),
            output_format="markdown",
            table_summary=table_summary,
            output_structure=output_structure
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parse result: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
