"""
Async parsing endpoints with progress tracking.

Provides background parsing jobs with real-time progress updates.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from pathlib import Path
import logging
import asyncio
import json
import time
from datetime import datetime

from app.config import DOCU_FOLDER
from app.models import ParseRequest
from app.job_manager import job_manager, JobStatus
from app.database import get_db
from app.services.dolphin_remote import parse_with_dolphin_remote, DOLPHIN_REMOTE_AVAILABLE
from app import crud, schemas
from app.utils.parsing_db import (
    create_or_update_document_record,
    save_parsing_success,
    save_parsing_failure
)
from app.utils.file_utils import (
    generate_version_folder_name,
    create_versioned_output_dir
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def _run_parsing_job(job_id: str, request: ParseRequest, db: Session):
    """
    Background task for parsing documents with progress tracking

    Args:
        job_id: Job identifier
        request: Parse request
        db: Database session
    """
    from app.config import DOCU_FOLDER, OUTPUT_FOLDER
    from app.services.mineru_parser import parse_with_mineru, MINERU_AVAILABLE
    from app.services.remote_ocr_parser import parse_with_remote_ocr, REMOTE_OCR_AVAILABLE
    from pathlib import Path

    start_time = time.time()
    db_document = None
    strategy = None

    try:
        # Update job status to processing
        job_manager.update_progress(
            job_id,
            status=JobStatus.PROCESSING,
            progress=10,
            message="🚀 Starting document parsing..."
        )

        # Progress callback function
        def update_progress(progress: int, message: str):
            """Update job progress via job_manager"""
            job_manager.update_progress(job_id, progress=progress, message=message)

        # Get file path and options
        file_path = DOCU_FOLDER / request.filename
        opts = request.get_options()

        # Create or update Document record in database (status=processing)
        db_document = create_or_update_document_record(db, request.filename, file_path)

        # Route to appropriate parser with progress callback
        is_pdf = file_path.suffix.lower() == '.pdf'

        # Remote OCR parsing (Korean optimized, scanned PDFs/images)
        if opts.use_remote_ocr and REMOTE_OCR_AVAILABLE:
            strategy = f'Remote OCR ({opts.remote_ocr_engine or "paddleocr"})'

            # Generate version folder name
            version_folder = generate_version_folder_name(
                strategy=strategy,
                options={
                    "remote_ocr_engine": opts.remote_ocr_engine or "paddleocr",
                    "remote_ocr_languages": opts.remote_ocr_languages or ["kor", "eng"]
                }
            )

            # Create versioned output directory
            doc_output_dir = create_versioned_output_dir(
                file_path=file_path,
                base_dir=OUTPUT_FOLDER,
                version_folder=version_folder
            )

            # Run Remote OCR in separate thread to avoid blocking event loop
            update_progress(15, "Starting Remote OCR processing...")

            ocr_langs = opts.remote_ocr_languages or ["kor", "eng"]
            content, metadata = await asyncio.to_thread(
                parse_with_remote_ocr,
                file_path,
                ocr_engine=opts.remote_ocr_engine or "paddleocr",
                ocr_languages=ocr_langs,
                output_dir=doc_output_dir if opts.save_to_output_folder else None,
                progress_callback=update_progress
            )

            # Build result
            from app.models import ParseResponse, ParsingMetadata

            # Save to database
            save_parsing_success(
                db=db,
                db_document=db_document,
                strategy=strategy,
                output_structure={
                    "output_dir": str(doc_output_dir),
                    "content_file": str(doc_output_dir / "content.md"),
                    "images_dir": None,
                    "tables_dir": None
                },
                duration_seconds=time.time() - start_time,
                options=opts,
                version_folder=version_folder,
                table_summary={
                    "parsing_method": "remote_ocr",
                    "ocr_engine": opts.remote_ocr_engine or "paddleocr",
                    "total_tables": 0
                },
                table_extractions=None,
                parsing_method="remote_ocr"
            )

            result = ParseResponse(
                success=True,
                filename=request.filename,
                markdown=content,
                stats={
                    "lines": content.count('\n') + 1,
                    "words": len(content.split()),
                    "characters": len(content),
                    "size_kb": round(len(content) / 1024, 2)
                },
                saved_to=str(doc_output_dir / "content.md"),
                output_format="markdown",
                table_summary={
                    "parsing_method": "remote_ocr",
                    "ocr_engine": opts.remote_ocr_engine or "paddleocr",
                    "ocr_languages": ocr_langs,
                    "total_pages": metadata.get("pages", 1),
                    "total_characters": metadata.get("characters_extracted", 0)
                },
                parsing_metadata=ParsingMetadata(
                    parser_used="remote_ocr",
                    table_parser=None,
                    ocr_enabled=True,
                    ocr_engine=f"remote-{opts.remote_ocr_engine or 'paddleocr'}",
                    output_format="markdown",
                    picture_description_enabled=False,
                    auto_image_analysis_enabled=False
                ),
                output_structure={
                    "output_dir": str(doc_output_dir),
                    "content_file": str(doc_output_dir / "content.md"),
                    "images_dir": None,
                    "tables_dir": None
                }
            )

        elif is_pdf and opts.use_dolphin and DOLPHIN_REMOTE_AVAILABLE:
            # Dolphin Remote GPU parsing with progress tracking
            strategy = f'Dolphin Remote GPU ({opts.dolphin_parsing_level or "normal"})'

            # Generate version folder name
            version_folder = generate_version_folder_name(
                strategy=strategy,
                options={
                    "dolphin_parsing_level": opts.dolphin_parsing_level or "normal",
                    "dolphin_max_batch_size": opts.dolphin_max_batch_size,
                    "output_format": opts.output_format
                }
            )

            # Create versioned output directory
            doc_output_dir = create_versioned_output_dir(
                file_path=file_path,
                base_dir=OUTPUT_FOLDER,
                version_folder=version_folder
            )

            # Run Dolphin Remote in separate thread to avoid blocking event loop
            content, metadata = await asyncio.to_thread(
                parse_with_dolphin_remote,
                file_path,
                output_dir=doc_output_dir if opts.save_to_output_folder else None,
                output_format=opts.output_format,
                parsing_level=opts.dolphin_parsing_level,
                max_batch_size=opts.dolphin_max_batch_size,
                progress_callback=update_progress
            )

            # Build result
            from app.models import ParseResponse, ParsingMetadata

            # Save to database
            save_parsing_success(
                db=db,
                db_document=db_document,
                strategy=strategy,
                output_structure={
                    "output_dir": str(doc_output_dir),
                    "content_file": str(doc_output_dir / "content.md"),
                    "images_dir": None,
                    "tables_dir": None
                },
                duration_seconds=time.time() - start_time,
                options=opts,
                version_folder=version_folder,
                table_summary={
                    "total_tables": metadata.get("tables", 0),
                    "parsing_method": "dolphin_remote"
                },
                table_extractions=None,
                parsing_method="dolphin_remote"
            )

            result = ParseResponse(
                success=True,
                filename=request.filename,
                markdown=content,
                stats={
                    "lines": content.count('\n') + 1,
                    "words": len(content.split()),
                    "characters": len(content),
                    "size_kb": round(len(content) / 1024, 2)
                },
                saved_to=str(doc_output_dir / "content.md"),
                output_format=opts.output_format,
                table_summary={
                    "total_tables": metadata.get("tables", 0),
                    "total_images": metadata.get("images", 0),
                    "total_formulas": metadata.get("formulas", 0),
                    "parsing_method": "dolphin_remote",
                    "gpu_server": metadata.get("gpu_server")
                },
                parsing_metadata=ParsingMetadata(
                    parser_used="dolphin_remote",
                    table_parser="dolphin_remote",
                    ocr_enabled=False,
                    output_format=opts.output_format
                )
            )

        elif is_pdf and opts.use_dolphin and not DOLPHIN_REMOTE_AVAILABLE:
            # Dolphin Remote GPU not available
            import os
            job_manager.update_progress(
                job_id,
                status=JobStatus.FAILED,
                progress=0,
                message=f"❌ Dolphin Remote GPU Server not available. Please check server connection: {os.getenv('DOLPHIN_GPU_SERVER', 'http://kca-ai.kro.kr:8005')}"
            )
            return

        elif is_pdf and opts.use_mineru and MINERU_AVAILABLE:
            # MinerU parsing with progress tracking
            strategy = f'MinerU ({"with OCR" if opts.mineru_use_ocr else "no OCR"})'

            # Generate version folder name
            version_folder = generate_version_folder_name(
                strategy=strategy,
                options={
                    "mineru_use_ocr": opts.mineru_use_ocr,
                    "mineru_lang": opts.mineru_lang,
                    "output_format": opts.output_format
                }
            )

            # Create versioned output directory
            doc_output_dir = create_versioned_output_dir(
                file_path=file_path,
                base_dir=OUTPUT_FOLDER,
                version_folder=version_folder
            )

            # Run blocking MinerU parser in separate thread to avoid blocking event loop
            content, metadata = await asyncio.to_thread(
                parse_with_mineru,
                file_path,
                output_dir=doc_output_dir,
                output_format=opts.output_format,
                lang=opts.mineru_lang,
                use_ocr=opts.mineru_use_ocr,
                progress_callback=update_progress
            )

            # Build result
            from app.models import ParseResponse, ParsingMetadata

            # Save to database
            save_parsing_success(
                db=db,
                db_document=db_document,
                strategy=strategy,
                output_structure={
                    "output_dir": str(doc_output_dir),
                    "content_file": str(doc_output_dir / "content.md"),
                    "images_dir": str(doc_output_dir / "images"),
                    "tables_dir": None
                },
                duration_seconds=time.time() - start_time,
                options=opts,
                version_folder=version_folder,
                table_summary={
                    "total_tables": metadata.get("tables", 0),
                    "parsing_method": "mineru"
                },
                table_extractions=None,
                parsing_method="mineru"
            )

            result = ParseResponse(
                success=True,
                filename=request.filename,
                markdown=content,
                stats={
                    "lines": content.count('\n') + 1,
                    "words": len(content.split()),
                    "characters": len(content),
                    "size_kb": round(len(content) / 1024, 2)
                },
                saved_to=str(doc_output_dir / "content.md"),
                output_format=opts.output_format,
                table_summary={
                    "total_tables": metadata.get("tables", 0),
                    "total_images": metadata.get("images", 0),
                    "parsing_method": "mineru"
                },
                parsing_metadata=ParsingMetadata(
                    parser_used="mineru",
                    table_parser="mineru",
                    ocr_enabled=opts.mineru_use_ocr,
                    output_format=opts.output_format
                )
            )

        else:
            # Fall back to sync parser (Docling/Camelot) - no progress tracking
            from app.api.parsing import parse_document as sync_parse
            result = await sync_parse(request, db)

        # Set result
        job_manager.update_progress(job_id, progress=95, message="✅ Finalizing...")
        job_manager.set_result(job_id, result.model_dump())
        job_manager.update_progress(job_id, message="✅ Parsing completed successfully!")

    except Exception as e:
        logger.error(f"Background parsing job {job_id} failed: {str(e)}", exc_info=True)
        job_manager.set_error(job_id, str(e))

        # Save failure to database
        save_parsing_failure(
            db=db,
            db_document=db_document,
            strategy=strategy if 'strategy' in locals() else None,
            error_message=str(e),
            duration_seconds=time.time() - start_time,
            options=request.get_options(),
            version_folder=version_folder if 'version_folder' in locals() else None
        )


@router.post("/parse/async")
async def parse_document_async(
    request: ParseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start asynchronous document parsing job

    Returns job_id immediately and processes document in background.
    Use GET /parse/status/{job_id} to check progress.

    Args:
        request: Parse request with filename and options
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Job information with job_id
    """
    try:
        file_path = DOCU_FOLDER / request.filename

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Create job
        job_id = job_manager.create_job(request.filename)

        # Add background task
        background_tasks.add_task(_run_parsing_job, job_id, request, db)

        logger.info(f"📋 Created parsing job {job_id} for {request.filename}")

        return {
            "success": True,
            "job_id": job_id,
            "filename": request.filename,
            "message": "Parsing job started. Use /parse/status/{job_id} to check progress."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating parsing job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parse/status/{job_id}")
async def get_parsing_status(job_id: str):
    """
    Get parsing job status and progress

    Args:
        job_id: Job identifier

    Returns:
        Job progress information
    """
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.job_id,
        "filename": job.filename,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "result": job.result,
        "error": job.error
    }
