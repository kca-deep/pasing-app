"""
Database query endpoints.

Provides access to document metadata, chunks, tables, and parsing history from the database.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app import crud, schemas

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/db/documents", response_model=List[schemas.DocumentSchema])
async def list_documents_db(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all documents from database with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by parsing status (pending, processing, completed, failed)
    """
    try:
        documents = crud.list_documents(db, skip=skip, limit=limit, status=status)

        # Add aggregated counts for each document
        result = []
        for doc in documents:
            doc_data = crud.get_document_with_counts(db, doc.id)
            doc_schema = schemas.DocumentSchema.model_validate(doc)
            doc_schema.chunk_count = doc_data["chunk_count"]
            doc_schema.table_count = doc_data["table_count"]
            doc_schema.picture_count = doc_data["picture_count"]
            result.append(doc_schema)

        return result
    except Exception as e:
        logger.error(f"Error listing documents from database: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/documents/{document_id}", response_model=schemas.DocumentDetailSchema)
async def get_document_detail(document_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific document, including related chunks, tables, and history.

    - **document_id**: Document ID from database
    """
    try:
        document = crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get related data
        tables = crud.get_tables_by_document_id(db, document_id)
        history = crud.get_parsing_history(db, document_id)
        pictures = crud.get_pictures_by_document_id(db, document_id)

        # Create detailed response
        doc_dict = schemas.DocumentSchema.model_validate(document).model_dump()
        doc_dict["tables"] = [schemas.TableSchema.model_validate(t) for t in tables]
        doc_dict["parsing_history"] = [schemas.ParsingHistorySchema.model_validate(h) for h in history]
        doc_dict["pictures"] = [schemas.PictureSchema.model_validate(p) for p in pictures]

        # Add counts
        doc_dict["chunk_count"] = 0
        doc_dict["table_count"] = len(tables)
        doc_dict["picture_count"] = len(pictures)

        return doc_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/documents/{document_id}/tables", response_model=List[schemas.TableSchema])
async def get_document_tables(document_id: int, db: Session = Depends(get_db)):
    """
    Get all tables for a specific document.

    - **document_id**: Document ID from database
    """
    try:
        # Check if document exists
        document = crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        tables = crud.get_tables_by_document_id(db, document_id)
        return [schemas.TableSchema.model_validate(t) for t in tables]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document tables: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/documents/{document_id}/history", response_model=List[schemas.ParsingHistorySchema])
async def get_document_history(document_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """
    Get parsing history for a specific document.

    - **document_id**: Document ID from database
    - **limit**: Maximum number of history records to return (default: 10)
    """
    try:
        # Check if document exists
        document = crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        history = crud.get_parsing_history(db, document_id, limit=limit)
        return [schemas.ParsingHistorySchema.model_validate(h) for h in history]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parsing history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/db/documents/{document_id}")
async def delete_document_db(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document from the database (and all related records via cascade).

    Note: This does NOT delete the physical files. File cleanup must be done separately.

    - **document_id**: Document ID from database
    """
    try:
        success = crud.delete_document(db, document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
