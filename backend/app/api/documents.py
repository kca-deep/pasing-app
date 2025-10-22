"""
Document management endpoints.

Handles document listing, uploading, and downloading.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
import logging

from app.config import DOCU_FOLDER
from app.models import DocumentInfo

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List documents in docu folder"""
    try:
        documents = []
        for file_path in DOCU_FOLDER.iterdir():
            if file_path.is_file() and file_path.suffix in ['.pdf', '.docx', '.pptx', '.html']:
                documents.append(DocumentInfo(
                    filename=file_path.name,
                    size=file_path.stat().st_size,
                    extension=file_path.suffix
                ))
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a document to the docu folder"""
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = ['.pdf', '.docx', '.pptx', '.html']

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed types: {', '.join(allowed_extensions)}"
            )

        # Save file to docu folder
        file_path = DOCU_FOLDER / file.filename

        # Read and write file content
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"📤 File uploaded: {file.filename} ({len(content)} bytes)")

        return {
            "success": True,
            "filename": file.filename,
            "size": len(content),
            "message": f"File {file.filename} uploaded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_markdown(filename: str):
    """Download converted Markdown file"""
    file_path = DOCU_FOLDER / filename

    if not file_path.exists() or not filename.endswith('.md'):
        raise HTTPException(status_code=404, detail="Markdown file not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/markdown'
    )
