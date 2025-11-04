"""
Dify Knowledge Base integration API endpoints.
"""
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, db_models, schemas
from app.database import get_db
from app.config import OUTPUT_FOLDER
from app.models import (
    DifyConfigModel,
    DifyDataset,
    DifyUploadRequest,
    DifyUploadResponse,
    ParsedDocumentInfo,
    IndexingStatusResponse
)
from app.services.dify_service import DifyClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dify", tags=["dify"])


# Helper function to get Dify client
async def get_dify_client(db: Session = Depends(get_db)) -> DifyClient:
    """
    Get Dify client from database configuration.

    Raises:
        HTTPException: If no configuration is found
        ValueError: If API key is invalid
    """
    config = crud.get_dify_config(db)
    if not config:
        raise HTTPException(
            status_code=404,
            detail="Dify configuration not found. Please configure Dify API settings first."
        )

    # Validate API key before creating client
    if not config.api_key or not config.api_key.strip():
        raise ValueError("Dify API key is empty. Please update your configuration.")

    try:
        client = DifyClient(api_key=config.api_key, base_url=config.base_url)
        return client
    except ValueError as e:
        # Re-raise ValueError with more context
        raise ValueError(f"Failed to initialize Dify client: {str(e)}")


@router.get("/config", response_model=DifyConfigModel)
async def get_config(db: Session = Depends(get_db)):
    """
    Get stored Dify API configuration.

    Returns:
        DifyConfigModel with API key and base URL
    """
    logger.info("📋 Getting Dify configuration")
    config = crud.get_dify_config(db)

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Dify configuration not found"
        )

    return DifyConfigModel(
        api_key=config.api_key,
        base_url=config.base_url
    )


@router.post("/config")
async def save_config(
    config: DifyConfigModel,
    db: Session = Depends(get_db)
):
    """
    Save or update Dify API configuration.

    Args:
        config: DifyConfigModel with API key and base URL

    Returns:
        Success message
    """
    logger.info(f"💾 Saving Dify configuration (base_url={config.base_url})")

    try:
        crud.create_or_update_dify_config(
            db=db,
            api_key=config.api_key,
            base_url=config.base_url
        )
        return {"success": True, "message": "Configuration saved successfully"}

    except Exception as e:
        logger.error(f"❌ Error saving configuration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.post("/test-connection")
async def test_connection(
    config: DifyConfigModel
):
    """
    Test connection to Dify API.

    Args:
        config: DifyConfigModel with API key and base URL

    Returns:
        Success status and message
    """
    logger.info("🔍 Testing Dify API connection")

    # Validate API key
    if not config.api_key or not config.api_key.strip():
        return {
            "success": False,
            "message": "API key is required. Please enter your Dify API key."
        }

    try:
        client = DifyClient(api_key=config.api_key, base_url=config.base_url)
    except ValueError as e:
        return {
            "success": False,
            "message": str(e)
        }

    try:
        success = await client.test_connection()

        if success:
            return {
                "success": True,
                "message": "Connection successful"
            }
        else:
            return {
                "success": False,
                "message": "Connection failed. Please check your API key and base URL."
            }

    except Exception as e:
        logger.error(f"❌ Connection test error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Connection error: {str(e)}"
        }
    finally:
        await client.close()


@router.get("/datasets", response_model=List[DifyDataset])
async def list_datasets(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List all datasets in Dify Knowledge Base.

    Args:
        page: Page number (1-indexed)
        limit: Number of datasets per page

    Returns:
        List of DifyDataset objects
    """
    logger.info(f"📋 Listing Dify datasets (page={page}, limit={limit})")

    # Get Dify client (with validation)
    try:
        client = await get_dify_client(db)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid API configuration: {str(e)}"
        )

    try:
        datasets = await client.list_datasets(page=page, limit=limit)
        return datasets

    finally:
        await client.close()


@router.get("/parsed-documents", response_model=List[ParsedDocumentInfo])
async def list_parsed_documents(db: Session = Depends(get_db)):
    """
    List all parsed documents with database metadata.

    Queries database for completed documents and enriches with file information.

    Returns:
        List of ParsedDocumentInfo objects with database metadata
    """
    logger.info("📂 Fetching parsed documents from database")

    try:
        # Query documents from database with counts (completed status only)
        db_documents = crud.list_documents_with_counts(
            db,
            limit=1000,
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

            # Get content.md file path and stats
            if not document.content_md_path:
                logger.warning(f"⚠️ Document {document.filename} has no content_md_path, skipping")
                continue

            content_file = Path(document.content_md_path)
            if not content_file.exists():
                logger.warning(f"⚠️ Content file not found: {content_file}, skipping")
                continue

            try:
                # Get file stats
                stat = content_file.stat()

                # Use original filename with .md extension for Dify upload
                # Instead of "content.md", use "original_filename.md"
                original_name_without_ext = Path(document.filename).stem
                dify_filename = f"{original_name_without_ext}.md"

                doc = ParsedDocumentInfo(
                    # File info (for Dify upload)
                    path=str(content_file.absolute()),
                    name=dify_filename,
                    size=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),

                    # Database metadata
                    id=document.id,
                    filename=document.filename,
                    file_extension=document.file_extension,
                    file_size=document.file_size,
                    total_pages=document.total_pages,
                    parsing_status=document.parsing_status,
                    parsing_strategy=document.parsing_strategy,
                    last_parsed_at=document.last_parsed_at.isoformat() if document.last_parsed_at else None,

                    # Aggregated counts
                    chunk_count=chunk_count,
                    table_count=table_count,
                    picture_count=picture_count
                )
                parsed_docs.append(doc)

            except Exception as e:
                logger.error(f"❌ Error processing document {document.filename}: {str(e)}")
                continue

        logger.info(f"✅ Returning {len(parsed_docs)} parsed documents with metadata")
        return parsed_docs

    except Exception as e:
        logger.error(f"❌ Error fetching parsed documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch parsed documents: {str(e)}")


@router.post("/upload", response_model=DifyUploadResponse)
async def upload_document(
    request: DifyUploadRequest,
    db: Session = Depends(get_db)
):
    """
    Upload a parsed document to Dify Knowledge Base.

    Args:
        request: DifyUploadRequest with dataset_id, document_path, and document_name

    Returns:
        DifyUploadResponse with document ID, batch ID, and indexing status
    """
    logger.info(f"📤 Uploading document '{request.document_name}' to dataset {request.dataset_id}")

    # Validate file exists
    file_path = Path(request.document_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.document_path}")

    # Read file content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"❌ Error reading file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    # Get Dify client
    client = await get_dify_client(db)

    try:
        # Get dataset name (for logging)
        datasets = await client.list_datasets(page=1, limit=100)
        dataset_name = None
        for ds in datasets:
            if ds.id == request.dataset_id:
                dataset_name = ds.name
                break

        # Upload document
        response = await client.create_document_by_text(
            dataset_id=request.dataset_id,
            name=request.document_name,
            text=content,
            indexing_technique=request.indexing_technique
        )

        # Create upload log
        crud.create_upload_log(
            db=db,
            dataset_id=request.dataset_id,
            dataset_name=dataset_name,
            document_path=request.document_path,
            document_name=request.document_name,
            dify_document_id=response.document_id,
            batch_id=response.batch
        )

        logger.info(f"✅ Document uploaded successfully (batch={response.batch})")
        return response

    finally:
        await client.close()


@router.get("/status/{dataset_id}/{batch_id}", response_model=IndexingStatusResponse)
async def get_indexing_status(
    dataset_id: str,
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    Check indexing status of a document batch.

    Args:
        dataset_id: Dataset ID
        batch_id: Batch ID from upload response

    Returns:
        IndexingStatusResponse with indexing status and progress
    """
    logger.info(f"🔍 Checking indexing status for batch {batch_id}")

    client = await get_dify_client(db)

    try:
        status = await client.check_indexing_status(
            dataset_id=dataset_id,
            batch_id=batch_id
        )

        # Update upload log if completed
        if status.indexing_status in ["completed", "error"]:
            # Find log by batch_id
            logs = crud.get_upload_history(db, limit=100)
            for log in logs:
                if log.batch_id == batch_id:
                    crud.update_upload_log(
                        db=db,
                        log_id=log.id,
                        indexing_status=status.indexing_status,
                        completed_at=datetime.utcnow()
                    )
                    break

        return status

    finally:
        await client.close()


@router.get("/upload-history", response_model=List[schemas.DifyUploadLogSchema])
async def get_upload_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get upload history.

    Args:
        limit: Maximum number of records to return

    Returns:
        List of DifyUploadLogSchema objects
    """
    logger.info(f"📜 Getting upload history (limit={limit})")

    logs = crud.get_upload_history(db, limit=limit)
    return logs
