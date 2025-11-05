"""
Database helper functions for parsing operations.

Provides centralized DB save logic to avoid code duplication between
parsing.py and async_parsing.py.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app import crud, schemas

logger = logging.getLogger(__name__)


def create_or_update_document_record(
    db: Session,
    filename: str,
    file_path: Path
) -> Optional[Any]:
    """
    Create or update Document record in database with processing status.

    Args:
        db: Database session
        filename: Document filename
        file_path: Full file path

    Returns:
        Document record or None if DB operation fails
    """
    try:
        doc_create = schemas.DocumentCreate(
            filename=filename,
            original_path=str(file_path.absolute()),
            file_size=file_path.stat().st_size,
            file_extension=file_path.suffix.lower(),
            parsing_status="processing"
        )

        # Check if document already exists
        existing_doc = crud.get_document_by_filename(db, filename)
        if existing_doc:
            # Update existing document
            db_document = existing_doc
            crud.update_document(db, existing_doc.id, schemas.DocumentUpdate(
                parsing_status="processing",
                last_parsed_at=datetime.utcnow()
            ))
            logger.info(f"📝 Updated existing document record (ID: {db_document.id})")
        else:
            # Create new document
            db_document = crud.create_document(db, doc_create)
            logger.info(f"📝 Created new document record (ID: {db_document.id})")

        return db_document

    except Exception as e:
        logger.error(f"Error creating/updating document record: {str(e)}", exc_info=True)
        return None


def save_parsing_success(
    db: Session,
    db_document: Any,
    strategy: str,
    output_structure: Optional[Dict[str, Any]],
    duration_seconds: float,
    options: Any,
    version_folder: Optional[str] = None,
    table_summary: Optional[Dict[str, Any]] = None,
    table_extractions: Optional[List[Dict[str, Any]]] = None,
    parsing_method: str = "docling"
) -> bool:
    """
    Save parsing success to database with version management.

    Updates Document record to completed status and creates ParsingHistory.
    Optionally saves Table metadata if table_extractions provided.

    Args:
        db: Database session
        db_document: Document record
        strategy: Parser strategy name (e.g., "Docling", "Remote OCR")
        output_structure: Output folder structure dict
        duration_seconds: Parsing duration in seconds
        options: Parsing options (TableParsingOptions or dict)
        version_folder: Version folder name (NEW - for version management)
        table_summary: Table summary dict (optional)
        table_extractions: List of extracted tables (optional)
        parsing_method: Table parsing method ("camelot" or "docling")

    Returns:
        True if successful, False otherwise
    """
    if not db_document:
        return False

    try:
        # Update document metadata
        doc_update = schemas.DocumentUpdate(
            parsing_status="completed",
            parsing_strategy=strategy,
            last_parsed_at=datetime.utcnow()
        )

        if output_structure:
            doc_update.output_folder = output_structure.get("output_dir")
            doc_update.content_md_path = output_structure.get("content_file")

        crud.update_document(db, db_document.id, doc_update)

        # Save table metadata to database
        if table_summary and table_extractions:
            try:
                table_creates = []
                for idx, table_data in enumerate(table_extractions):
                    table_info = table_data.get("table_info", {})
                    table_create = schemas.TableCreate(
                        document_id=db_document.id,
                        table_id=f"table_{idx+1:03d}",
                        table_index=idx,
                        page=table_info.get("page"),
                        caption=table_info.get("caption"),
                        rows=table_info.get("rows"),
                        cols=table_info.get("cols"),
                        has_merged_cells=table_info.get("has_merged_cells", False),
                        is_complex=table_info.get("is_complex", False),
                        complexity_score=table_info.get("complexity_score"),
                        json_path=table_data.get("json_path"),
                        parsing_method=parsing_method
                    )
                    table_creates.append(table_create)

                if table_creates:
                    crud.create_tables_bulk(db, table_creates)
                    logger.info(f"  💾 Saved {len(table_creates)} tables to database")
            except Exception as e:
                logger.error(f"Error saving table metadata: {str(e)}", exc_info=True)

        # Mark previous versions as not latest
        if version_folder:
            try:
                from app import db_models
                db.query(db_models.ParsingHistory).filter(
                    db_models.ParsingHistory.document_id == db_document.id,
                    db_models.ParsingHistory.is_latest == True
                ).update({"is_latest": False})
                db.commit()
            except Exception as e:
                logger.warning(f"Error updating previous versions: {str(e)}")

        # Create ParsingHistory record with version info
        try:
            # Convert options to dict if needed
            if hasattr(options, 'model_dump'):
                options_json = json.dumps(options.model_dump())
            elif isinstance(options, dict):
                options_json = json.dumps(options)
            else:
                options_json = json.dumps({})

            history_create = schemas.ParsingHistoryCreate(
                document_id=db_document.id,
                parsing_status="completed",
                parsing_strategy=strategy,
                options_json=options_json,
                version_folder=version_folder,
                output_dir=output_structure.get("output_dir") if output_structure else None,
                content_path=output_structure.get("content_file") if output_structure else None,
                metadata_path=str(Path(output_structure.get("output_dir")) / "metadata.json") if output_structure else None,
                is_latest=True,
                total_tables=table_summary.get("total_tables", 0) if table_summary else 0,
                markdown_tables=table_summary.get("markdown_tables", 0) if table_summary else 0,
                json_tables=table_summary.get("json_tables", 0) if table_summary else 0,
                total_images=table_summary.get("total_images", 0) if table_summary else 0,
                duration_seconds=duration_seconds
            )
            crud.create_parsing_history(db, history_create)
            logger.info(f"  💾 Created parsing history record (version: {version_folder}, duration: {duration_seconds:.2f}s)")
        except Exception as e:
            logger.error(f"Error creating parsing history: {str(e)}", exc_info=True)

        return True

    except Exception as e:
        logger.error(f"Error updating database after parsing: {str(e)}", exc_info=True)
        return False


def save_parsing_failure(
    db: Session,
    db_document: Any,
    strategy: Optional[str],
    error_message: str,
    duration_seconds: float,
    options: Any,
    version_folder: Optional[str] = None
) -> bool:
    """
    Save parsing failure to database with version management.

    Updates Document record to failed status and creates ParsingHistory with error.

    Args:
        db: Database session
        db_document: Document record
        strategy: Parser strategy name (or None if not determined)
        error_message: Error message string
        duration_seconds: Parsing duration in seconds
        options: Parsing options (TableParsingOptions or dict)
        version_folder: Version folder name (NEW - for version management)

    Returns:
        True if successful, False otherwise
    """
    if not db_document:
        return False

    try:
        # Update document status to failed
        crud.update_document(db, db_document.id, schemas.DocumentUpdate(
            parsing_status="failed",
            last_parsed_at=datetime.utcnow()
        ))

        # Create ParsingHistory record with error
        try:
            # Convert options to dict if needed
            if hasattr(options, 'model_dump'):
                options_json = json.dumps(options.model_dump())
            elif isinstance(options, dict):
                options_json = json.dumps(options)
            else:
                options_json = json.dumps({})

            history_create = schemas.ParsingHistoryCreate(
                document_id=db_document.id,
                parsing_status="failed",
                parsing_strategy=strategy if strategy else "unknown",
                options_json=options_json,
                version_folder=version_folder,
                is_latest=False,  # Failed attempts are not marked as latest
                error_message=error_message,
                duration_seconds=duration_seconds
            )
            crud.create_parsing_history(db, history_create)
            logger.info(f"  💾 Updated document to failed status and created error history (version: {version_folder})")
        except Exception as e:
            logger.error(f"Error creating error history: {str(e)}", exc_info=True)

        return True

    except Exception as e:
        logger.error(f"Error updating database after parsing failure: {str(e)}", exc_info=True)
        return False
