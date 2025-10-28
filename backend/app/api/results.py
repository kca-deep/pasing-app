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
    """List all parsed documents in the output folder"""
    logger.info("=" * 80)
    logger.info("🔵 RESULTS.PY CODE VERSION: 2024-10-27-v3 WITH DATABASE FALLBACK")
    logger.info("=" * 80)
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

                        # Load parsing metadata if available
                        parsing_metadata = None
                        debug_info = {}

                        metadata_file = doc_dir / "metadata.json"
                        debug_info["metadata_file_path"] = str(metadata_file)
                        debug_info["metadata_file_exists"] = metadata_file.exists()

                        if metadata_file.exists():
                            try:
                                with open(metadata_file, 'r', encoding='utf-8') as mf:
                                    metadata_dict = json.load(mf)
                                    parsing_metadata = metadata_dict  # Keep as dict for JSON response
                                debug_info["metadata_source"] = "file"
                            except Exception as e:
                                logger.error(f"Error loading metadata for {doc_dir.name}: {str(e)}")
                                debug_info["file_read_error"] = str(e)
                        else:
                            # Fallback to database if metadata.json doesn't exist
                            # Try to find document in database by matching output folder name
                            debug_info["metadata_source"] = "database_fallback"
                            try:
                                logger.info(f"🔍 Trying to load metadata from database for {doc_dir.name}")
                                db_doc = None
                                debug_info["extensions_tried"] = []

                                # Try common extensions
                                for ext in ['.pdf', '.docx', '.pptx', '.html', '.txt']:
                                    filename_to_try = doc_dir.name + ext
                                    debug_info["extensions_tried"].append(filename_to_try)
                                    db_doc = crud.get_document_by_filename(db, filename_to_try)
                                    if db_doc:
                                        logger.info(f"✓ Found document in DB with extension {ext}")
                                        debug_info["db_document_found"] = True
                                        debug_info["db_filename"] = db_doc.filename
                                        debug_info["db_strategy"] = db_doc.parsing_strategy
                                        break

                                if db_doc and db_doc.parsing_strategy:
                                    # Create metadata from database info
                                    parsing_metadata = {
                                        "parser_used": _map_strategy_to_parser(db_doc.parsing_strategy),
                                        "table_parser": None,
                                        "ocr_enabled": False,
                                        "ocr_engine": None,
                                        "output_format": "markdown",
                                        "picture_description_enabled": False,
                                        "auto_image_analysis_enabled": False
                                    }
                                    debug_info["metadata_generated"] = True
                                    logger.info(f"📊 Generated metadata from database for {doc_dir.name}: {parsing_metadata}")
                                else:
                                    debug_info["db_document_found"] = False
                                    logger.warning(f"⚠️ Document not found in DB or no strategy for {doc_dir.name}")
                            except Exception as e:
                                debug_info["db_error"] = str(e)
                                logger.error(f"❌ Error loading metadata from DB for {doc_dir.name}: {str(e)}", exc_info=True)

                        parsed_docs.append({
                            "document_name": doc_dir.name,
                            "parsed_at": stat.st_mtime,
                            "size_kb": round(stat.st_size / 1024, 2),
                            "preview": preview,
                            "table_count": table_count,
                            "output_dir": str(doc_dir),
                            "parsing_metadata": parsing_metadata,
                            "_debug": debug_info  # Debug information
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
