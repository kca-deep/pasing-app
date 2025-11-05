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
async def list_parsed_documents(
    db: Session = Depends(get_db),
    show_all_versions: bool = True  # Show all parsing versions by default
):
    """
    List all parsed documents from database with version support.

    Args:
        show_all_versions: If True, show all parsing versions. If False, show only latest version per document.
    """
    logger.info("=" * 80)
    logger.info("🔵 RESULTS.PY CODE VERSION: 2025-11-05 VERSION-AWARE LISTING")
    logger.info("=" * 80)
    try:
        from app import db_models

        # Query parsing histories with completed status
        if show_all_versions:
            # Show all completed parsing attempts
            query = db.query(db_models.ParsingHistory).filter(
                db_models.ParsingHistory.parsing_status == "completed"
            ).order_by(db_models.ParsingHistory.created_at.desc())
        else:
            # Show only latest version per document
            query = db.query(db_models.ParsingHistory).filter(
                db_models.ParsingHistory.parsing_status == "completed",
                db_models.ParsingHistory.is_latest == True
            ).order_by(db_models.ParsingHistory.created_at.desc())

        parsing_histories = query.limit(100).all()

        logger.info(f"📊 Found {len(parsing_histories)} parsing histories (show_all_versions={show_all_versions})")

        parsed_docs = []

        for history in parsing_histories:
            # Get associated document
            document = crud.get_document_by_id(db, history.document_id)
            if not document:
                continue

            # Get table count for this specific version
            table_count = history.json_tables or 0
            picture_count = history.total_images or 0

            # Get file preview if content file exists
            preview = ""
            content_size_kb = 0

            if history.content_path:
                content_file = Path(history.content_path)
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
            if history.metadata_path and Path(history.metadata_path).exists():
                try:
                    with open(history.metadata_path, 'r', encoding='utf-8') as mf:
                        parsing_metadata = json.load(mf)
                except Exception as e:
                    logger.error(f"Error loading metadata for {document.filename}: {str(e)}")

            # If no metadata file, generate from options_json
            if not parsing_metadata and history.options_json:
                try:
                    options = json.loads(history.options_json)
                    parsing_metadata = {
                        "parser_used": _map_strategy_to_parser(history.parsing_strategy),
                        "table_parser": options.get("table_parser"),
                        "ocr_enabled": options.get("do_ocr", False),
                        "ocr_engine": options.get("ocr_engine"),
                        "output_format": options.get("output_format", "markdown"),
                        "picture_description_enabled": options.get("do_picture_description", False),
                        "auto_image_analysis_enabled": options.get("auto_image_analysis", False)
                    }
                except Exception as e:
                    logger.error(f"Error parsing options_json: {str(e)}")

            # Build response object
            parsed_docs.append({
                # Primary display fields
                "filename": document.filename,  # Original filename as title
                "document_name": Path(document.filename).stem,  # Name without extension

                # Version info (NEW)
                "version_folder": history.version_folder,
                "version_id": history.id,
                "is_latest": history.is_latest,

                # Database metadata
                "id": history.id,  # Parsing History ID (unique across all versions)
                "document_id": document.id,  # Document ID (same for all versions of same file)
                "file_extension": document.file_extension,
                "file_size": document.file_size,  # Original file size in bytes
                "total_pages": document.total_pages,
                "parsing_status": history.parsing_status,
                "parsing_strategy": history.parsing_strategy,
                "created_at": document.created_at.timestamp() if document.created_at else None,
                "updated_at": document.updated_at.timestamp() if document.updated_at else None,
                "last_parsed_at": document.last_parsed_at.timestamp() if document.last_parsed_at else None,
                "parsed_at": history.created_at.timestamp() if history.created_at else None,
                "duration_seconds": history.duration_seconds,

                # Version-specific counts
                "chunk_count": 0,  # Chunk is not used
                "table_count": table_count,
                "picture_count": picture_count,

                # File metadata
                "size_kb": content_size_kb,  # Parsed content file size
                "preview": preview,
                "output_dir": history.output_dir,

                # Parsing metadata
                "parsing_metadata": parsing_metadata,
            })

        logger.info(f"✅ Returning {len(parsed_docs)} parsing results with version info")

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

        # Try to get document from database first
        db_doc = crud.get_document_by_filename(db, filename)

        # Find content file path
        content_file = None
        doc_output_dir = OUTPUT_FOLDER / doc_name

        # Strategy 1: Use content_md_path from database
        if db_doc and db_doc.content_md_path:
            content_file = Path(db_doc.content_md_path)
            if not content_file.exists():
                logger.warning(f"⚠️ DB content_md_path exists but file not found: {content_file}")
                content_file = None

        # Strategy 2: Check direct path (old structure)
        if not content_file:
            direct_path = doc_output_dir / "content.md"
            if direct_path.exists():
                content_file = direct_path

        # Strategy 3: Find latest version folder (new structure)
        if not content_file and doc_output_dir.exists():
            version_folders = [d for d in doc_output_dir.iterdir() if d.is_dir()]
            if version_folders:
                # Sort by modification time (newest first)
                version_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for version_folder in version_folders:
                    content_candidate = version_folder / "content.md"
                    if content_candidate.exists():
                        content_file = content_candidate
                        doc_output_dir = version_folder  # Update to version folder
                        break

        if not content_file or not content_file.exists():
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
