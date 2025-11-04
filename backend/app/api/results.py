"""
Parsed results endpoints.

Handles listing and retrieving previously parsed documents.
"""

from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
import logging
import json
from sqlalchemy.orm import Session

from app.config import OUTPUT_FOLDER
from app.models import ParseResponse, ParsingMetadata
from app.database import get_db
from app import crud

router = APIRouter()
logger = logging.getLogger(__name__)


def _map_strategy_to_parser(strategy: str) -> str:
    """Map database parsing_strategy to parser_used name"""
    strategy_lower = strategy.lower()

    if "dolphin" in strategy_lower:
        return "dolphin"
    elif "mineru" in strategy_lower:
        return "mineru"
    elif "remote" in strategy_lower and "ocr" in strategy_lower:
        return "remote_ocr"
    elif "camelot" in strategy_lower and "docling" not in strategy_lower:
        return "camelot"
    else:
        return "docling"


@router.get("/parsed-documents")
async def list_parsed_documents(db: Session = Depends(get_db)):
    """List all parsed documents from database with file metadata enrichment"""
    logger.info("=" * 80)
    logger.info("🔵 RESULTS.PY CODE VERSION: 2024-10-29-v4 DATABASE-FIRST WITH FILE ENRICHMENT")
    logger.info("=" * 80)
    try:
        # Query documents from database with counts (completed status only)
        db_documents = crud.list_documents_with_counts(
            db,
            limit=100,
            status="completed",
            order_by="last_parsed_at"
        )

        logger.info(f"📊 Found {len(db_documents)} completed documents in database")

        parsed_docs = []

        for doc_info in db_documents:
            document = doc_info["document"]
            chunk_count = doc_info["chunk_count"]
            table_count = doc_info["table_count"]
            picture_count = doc_info["picture_count"]

            # Get file preview if content file exists
            preview = ""
            content_size_kb = 0

            if document.content_md_path:
                content_file = Path(document.content_md_path)
                if content_file.exists():
                    try:
                        # Read first few lines for preview
                        with open(content_file, 'r', encoding='utf-8') as f:
                            content = f.read(500)  # Read first 500 chars
                            preview = content[:200] + "..." if len(content) > 200 else content

                        # Get actual file size
                        stat = content_file.stat()
                        content_size_kb = round(stat.st_size / 1024, 2)
                    except Exception as e:
                        logger.error(f"Error reading content file for {document.filename}: {str(e)}")

            # Load parsing metadata if available
            parsing_metadata = None
            if document.output_folder:
                metadata_file = Path(document.output_folder) / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as mf:
                            parsing_metadata = json.load(mf)
                    except Exception as e:
                        logger.error(f"Error loading metadata for {document.filename}: {str(e)}")

            # If no metadata file, generate from database
            if not parsing_metadata and document.parsing_strategy:
                parsing_metadata = {
                    "parser_used": _map_strategy_to_parser(document.parsing_strategy),
                    "table_parser": None,
                    "ocr_enabled": False,
                    "ocr_engine": None,
                    "output_format": "markdown",
                    "picture_description_enabled": False,
                    "auto_image_analysis_enabled": False
                }

            # Build response object
            parsed_docs.append({
                # Primary display fields
                "filename": document.filename,  # Original filename as title
                "document_name": Path(document.filename).stem,  # Name without extension

                # Database metadata
                "id": document.id,
                "file_extension": document.file_extension,
                "file_size": document.file_size,  # Original file size in bytes
                "total_pages": document.total_pages,
                "parsing_status": document.parsing_status,
                "parsing_strategy": document.parsing_strategy,
                "created_at": document.created_at.timestamp() if document.created_at else None,
                "updated_at": document.updated_at.timestamp() if document.updated_at else None,
                "last_parsed_at": document.last_parsed_at.timestamp() if document.last_parsed_at else None,
                "parsed_at": document.last_parsed_at.timestamp() if document.last_parsed_at else document.updated_at.timestamp(),

                # Aggregated counts from database
                "chunk_count": chunk_count,
                "table_count": table_count,
                "picture_count": picture_count,

                # File metadata
                "size_kb": content_size_kb,  # Parsed content file size
                "preview": preview,
                "output_dir": document.output_folder,

                # Parsing metadata
                "parsing_metadata": parsing_metadata,
            })

        logger.info(f"✅ Returning {len(parsed_docs)} documents with enriched metadata")

        return {
            "total": len(parsed_docs),
            "documents": parsed_docs
        }

    except Exception as e:
        logger.error(f"Error listing parsed documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{filename}")
async def get_parse_result(filename: str, db: Session = Depends(get_db)):
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

        # Load parsing metadata if available
        parsing_metadata = None
        metadata_file = doc_output_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_dict = json.load(f)
                    parsing_metadata = ParsingMetadata(**metadata_dict)
                logger.info(f"📄 Loaded parsing metadata from {metadata_file}")
            except Exception as e:
                logger.error(f"Error loading metadata.json: {str(e)}", exc_info=True)
        else:
            # Fallback to database if metadata.json doesn't exist
            try:
                logger.info(f"🔍 Trying to load metadata from database for {filename}")
                db_doc = None

                # Try with filename as-is first
                db_doc = crud.get_document_by_filename(db, filename)

                # If not found, try adding common extensions (doc_name might not have extension)
                if not db_doc:
                    for ext in ['.pdf', '.docx', '.pptx', '.html', '.txt']:
                        filename_with_ext = doc_name + ext
                        db_doc = crud.get_document_by_filename(db, filename_with_ext)
                        if db_doc:
                            logger.info(f"✓ Found document in DB with extension {ext}")
                            break

                if db_doc and db_doc.parsing_strategy:
                    # Create metadata from database info
                    parsing_metadata = ParsingMetadata(
                        parser_used=_map_strategy_to_parser(db_doc.parsing_strategy),
                        table_parser=None,
                        ocr_enabled=False,
                        ocr_engine=None,
                        output_format="markdown",
                        picture_description_enabled=False,
                        auto_image_analysis_enabled=False
                    )
                    logger.info(f"📊 Generated metadata from database for {filename}: parser={parsing_metadata.parser_used}")
                else:
                    logger.warning(f"⚠️ Document not found in DB or no strategy for {filename}")
            except Exception as e:
                logger.error(f"❌ Error loading metadata from DB: {str(e)}", exc_info=True)

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
            output_structure=output_structure,
            parsing_metadata=parsing_metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parse result: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
