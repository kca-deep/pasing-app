"""
Document parsing endpoints.

Main parsing logic that orchestrates Docling, Camelot, and VLM processing.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pathlib import Path
import logging
import time
import json
import os
from datetime import datetime

from app.config import DOCU_FOLDER, OUTPUT_FOLDER
from app.models import ParseRequest, ParseResponse, ParsingMetadata
from app.services.docling import parse_document_with_docling
from app.services.tables import integrate_camelot_tables_into_content
from app.services.pictures import filter_picture_descriptions_smart, extract_pictures_info
from app.services.mineru_parser import parse_with_mineru, check_mineru_installation, MINERU_AVAILABLE
from app.services.dolphin_remote import parse_with_dolphin_remote, DOLPHIN_REMOTE_AVAILABLE
from app.services.remote_ocr_parser import parse_with_remote_ocr, check_remote_ocr_parser_availability
from app.services.remote_ocr import REMOTE_OCR_AVAILABLE
from app.table_utils import (
    extract_tables_from_document,
    extract_tables_with_camelot,
    CAMELOT_AVAILABLE
)
from app.database import get_db
from app import crud, schemas

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/parse", response_model=ParseResponse)
async def parse_document(request: ParseRequest, db: Session = Depends(get_db)):
    """Parse document in docu folder to Markdown/HTML/JSON using Docling library"""
    start_time = time.time()
    db_document = None
    warnings = []  # Collect warnings for user

    try:
        file_path = DOCU_FOLDER / request.filename

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Create Document record in database (status=processing)
        try:
            doc_create = schemas.DocumentCreate(
                filename=request.filename,
                original_path=str(file_path.absolute()),
                file_size=file_path.stat().st_size,
                file_extension=file_path.suffix.lower(),
                parsing_status="processing"
            )

            # Check if document already exists
            existing_doc = crud.get_document_by_filename(db, request.filename)
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
        except Exception as e:
            logger.error(f"Error creating/updating document record: {str(e)}", exc_info=True)
            # Continue without DB (non-blocking)

        # Get parsing options
        opts = request.get_options()

        # Auto-select parsing strategy based on file type
        is_pdf = file_path.suffix.lower() == '.pdf'

        # 🆕 Remote OCR 사용 (한글 문서 최적화, 스캔된 PDF/이미지)
        if opts.use_remote_ocr and REMOTE_OCR_AVAILABLE:
            strategy = f'Remote OCR ({opts.remote_ocr_engine})'
            logger.info(f"📄 Parsing: {request.filename} | Strategy: {strategy}")

            # Create output directory for this document
            doc_name = file_path.stem
            doc_output_dir = OUTPUT_FOLDER / doc_name
            doc_output_dir.mkdir(parents=True, exist_ok=True)

            # Remote OCR로 파싱
            try:
                ocr_langs = opts.remote_ocr_languages or ["kor", "eng"]
                content, remote_ocr_metadata = parse_with_remote_ocr(
                    file_path,
                    ocr_engine=opts.remote_ocr_engine,
                    ocr_languages=ocr_langs,
                    output_dir=doc_output_dir if opts.save_to_output_folder else None
                )

                # 메타데이터 변환
                table_summary = {
                    "parsing_method": "remote_ocr",
                    "ocr_engine": opts.remote_ocr_engine,
                    "ocr_languages": ocr_langs,
                    "total_pages": remote_ocr_metadata.get("pages", 1),
                    "total_characters": remote_ocr_metadata.get("characters_extracted", 0)
                }

                # Remote OCR은 텍스트만 추출
                table_extractions = []
                docling_doc = None

                # Parsing metadata
                parsing_metadata = ParsingMetadata(
                    parser_used="remote_ocr",
                    table_parser=None,
                    ocr_enabled=True,
                    ocr_engine=f"remote-{opts.remote_ocr_engine}",
                    output_format="markdown",  # Remote OCR는 항상 Markdown
                    picture_description_enabled=False,
                    auto_image_analysis_enabled=False
                )

                # output_structure 설정
                content_path = doc_output_dir / "content.md"
                output_structure = {
                    "output_dir": str(doc_output_dir),
                    "content_file": str(content_path),
                    "images_dir": None,
                    "tables_dir": None
                }
                output_path = content_path

                logger.info(f"✅ Remote OCR parsing completed ({opts.remote_ocr_engine})")

            except Exception as e:
                logger.error(f"Error during Remote OCR parsing: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Remote OCR parsing failed: {str(e)}")

        elif opts.use_remote_ocr and not REMOTE_OCR_AVAILABLE:
            # Remote OCR 요청했지만 서버 연결 안 됨 → 경고 후 fallback
            warnings.append(
                "Remote OCR Server not available. Falling back to Docling with EasyOCR."
            )
            logger.warning("⚠️ Remote OCR requested but server not available, falling back to Docling")
            # Continue to next strategy (Dolphin or Docling)
            opts.use_remote_ocr = False  # Disable for fallback

        # 🆕 Dolphin Remote GPU 사용 (AI-Powered, 고정밀도)
        elif is_pdf and opts.use_dolphin and DOLPHIN_REMOTE_AVAILABLE:
            strategy = 'Dolphin Remote GPU (AI-Powered)'
            logger.info(f"📄 Parsing: {request.filename} | Strategy: {strategy}")

            # Create output directory for this document
            doc_name = file_path.stem
            doc_output_dir = OUTPUT_FOLDER / doc_name
            doc_output_dir.mkdir(parents=True, exist_ok=True)

            # Dolphin Remote GPU로 파싱
            try:
                content, dolphin_metadata = parse_with_dolphin_remote(
                    file_path,
                    output_dir=doc_output_dir if opts.save_to_output_folder else None,
                    output_format=opts.output_format,
                    parsing_level=opts.dolphin_parsing_level,
                    max_batch_size=opts.dolphin_max_batch_size,
                    progress_callback=None  # No progress tracking in sync mode
                )

                # Dolphin 메타데이터를 table_summary로 변환
                table_summary = {
                    "total_tables": dolphin_metadata.get("tables", 0),
                    "total_images": dolphin_metadata.get("images", 0),
                    "total_formulas": dolphin_metadata.get("formulas", 0),
                    "parsing_method": "dolphin_remote",
                    "gpu_server": dolphin_metadata.get("gpu_server", "unknown"),
                    "model_version": "1.5",
                    "parsing_level": opts.dolphin_parsing_level
                }

                # Dolphin은 자체적으로 content를 처리하므로 별도 table_extractions 불필요
                table_extractions = []
                docling_doc = None  # Dolphin은 docling_doc 불필요

                # Parsing metadata for Dolphin Remote
                parsing_metadata = ParsingMetadata(
                    parser_used="dolphin_remote",
                    table_parser="dolphin_remote",
                    ocr_enabled=False,  # Dolphin은 AI 기반으로 OCR과 별개
                    output_format=opts.output_format,
                    dolphin_parsing_level=opts.dolphin_parsing_level,
                    picture_description_enabled=False,
                    auto_image_analysis_enabled=False
                )

                # output_structure 설정
                content_path = doc_output_dir / "content.md"
                output_structure = {
                    "output_dir": str(doc_output_dir),
                    "content_file": str(content_path),
                    "images_dir": None,
                    "tables_dir": None  # Dolphin은 표를 content.md에 통합
                }
                output_path = content_path

            except Exception as e:
                logger.error(f"Error during Dolphin Remote parsing: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Dolphin Remote parsing failed: {str(e)}")

        # Dolphin Local 제거됨 - Remote GPU만 사용
        elif is_pdf and opts.use_dolphin and not DOLPHIN_REMOTE_AVAILABLE:
            # Dolphin Remote GPU 서버 연결 실패 → 에러 반환
            error_msg = (
                "Dolphin Remote GPU Server not available.\n\n"
                "Please check:\n"
                "  1. GPU server is running and accessible\n"
                "  2. DOLPHIN_GPU_SERVER environment variable is set correctly\n"
                f"  3. Current server: {os.getenv('DOLPHIN_GPU_SERVER', 'http://kca-ai.kro.kr:8005')}\n\n"
                "Or use Remote OCR/MinerU/Camelot/Docling parsing strategy instead."
            )
            logger.error(f"❌ Dolphin Remote GPU requested but not available")
            raise HTTPException(status_code=400, detail=error_msg)

        # 🆕 MinerU 우선 사용 (범용 솔루션)
        elif is_pdf and opts.use_mineru and MINERU_AVAILABLE:
            strategy = 'MinerU (Universal)'
            logger.info(f"📄 Parsing: {request.filename} | Strategy: {strategy}")

            # Create output directory for this document
            doc_name = file_path.stem
            doc_output_dir = OUTPUT_FOLDER / doc_name
            doc_output_dir.mkdir(parents=True, exist_ok=True)

            # MinerU로 파싱 (로컬 라이브러리)
            try:
                content, mineru_metadata = parse_with_mineru(
                    file_path,
                    output_dir=doc_output_dir,
                    output_format=opts.output_format,
                    lang=opts.mineru_lang,
                    use_ocr=opts.mineru_use_ocr,
                    progress_callback=None  # No progress tracking in sync mode
                )

                # MinerU는 자체적으로 표를 처리하므로 table_summary는 MinerU 메타데이터 사용
                table_summary = {
                    "total_tables": mineru_metadata.get("tables", 0),
                    "total_images": mineru_metadata.get("images", 0),
                    "total_formulas": mineru_metadata.get("formulas", 0),
                    "parsing_method": "mineru",
                    "language": mineru_metadata.get("language"),
                    "ocr_enabled": mineru_metadata.get("ocr_enabled", False)
                }

                # MinerU는 자체적으로 표를 처리하므로 별도 table_extractions 불필요
                table_extractions = []

                docling_doc = None  # MinerU는 docling_doc 불필요

                # Parsing metadata for MinerU
                parsing_metadata = ParsingMetadata(
                    parser_used="mineru",
                    table_parser="mineru",
                    ocr_enabled=opts.mineru_use_ocr,
                    output_format=opts.output_format,
                    mineru_lang=opts.mineru_lang,
                    picture_description_enabled=False,
                    auto_image_analysis_enabled=False
                )

                # MinerU는 자체적으로 content.md를 생성하므로 output_structure 설정
                content_path = doc_output_dir / "content.md"
                output_structure = {
                    "output_dir": str(doc_output_dir),
                    "content_file": str(content_path),
                    "images_dir": str(doc_output_dir / "images"),
                    "tables_dir": None  # MinerU는 표를 content.md에 통합
                }
                output_path = content_path

            except Exception as e:
                logger.error(f"Error during MinerU parsing: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"MinerU parsing failed: {str(e)}")

        elif is_pdf and opts.use_mineru and not MINERU_AVAILABLE:
            # MinerU 요청했지만 설치 안 됨 → 에러 반환 (fallback 없음)
            error_msg = (
                "MinerU is not installed. Please install MinerU to use this feature.\n\n"
                "Installation command:\n"
                "  pip install magic-pdf[full]\n\n"
                "Or use Camelot/Docling parsing strategy instead."
            )
            logger.error(f"❌ MinerU requested but not available")
            raise HTTPException(status_code=400, detail=error_msg)

        else:
            # 기존 Camelot/Docling 로직 (MinerU 미사용)
            will_use_camelot = opts.use_camelot and is_pdf and CAMELOT_AVAILABLE

            if is_pdf and opts.use_camelot and not CAMELOT_AVAILABLE:
                logger.warning("⚠️ Camelot requested but not available. Falling back to Docling.")

            strategy = 'Docling+Camelot Hybrid' if will_use_camelot else 'Docling Only'
            logger.info(f"📄 Parsing: {request.filename} | Strategy: {strategy}")

            # Force Markdown table export when using Camelot (for compatibility)
            if will_use_camelot and opts.tables_as_html:
                logger.info("  Forcing tables_as_html=False for Camelot compatibility")
                opts.tables_as_html = False

            # Parse document using Docling library directly
            # Returns (content, docling_document) for Phase 3+ table extraction
            try:
                content, docling_doc = parse_document_with_docling(file_path, opts)
            except Exception as e:
                logger.error(f"Error during Docling parsing: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

            # Parsing metadata for Docling+Camelot
            parsing_metadata = ParsingMetadata(
                parser_used="docling",
                table_parser="camelot" if will_use_camelot else "docling",
                ocr_enabled=opts.do_ocr,
                ocr_engine=opts.ocr_engine if opts.do_ocr else None,
                output_format=opts.output_format,
                camelot_mode=opts.camelot_mode if will_use_camelot else None,
                picture_description_enabled=opts.do_picture_description,
                auto_image_analysis_enabled=opts.auto_image_analysis
            )

        # Phase 3: Extract tables if enabled
        # NOTE: MinerU 사용 시 table_summary와 output_structure가 이미 설정되어 있음
        if 'table_summary' not in locals():
            table_summary = None
        if 'output_structure' not in locals():
            output_structure = None
        if 'output_path' not in locals():
            output_path = None

        # MinerU를 사용한 경우 table extraction 스킵 (MinerU가 자동 처리)
        if opts.extract_tables and opts.save_to_output_folder and docling_doc and output_structure is None:
            try:
                # Create output directory for this document
                doc_name = file_path.stem
                doc_output_dir = OUTPUT_FOLDER / doc_name
                doc_output_dir.mkdir(parents=True, exist_ok=True)

                # Choose extraction method: Camelot (PDF, high accuracy) or Docling (all formats)
                if will_use_camelot:
                    # Use Camelot for PDF files (default behavior)
                    table_extractions, table_summary = extract_tables_with_camelot(
                        file_path,
                        doc_output_dir,
                        doc_name,
                        complexity_threshold=opts.table_complexity_threshold,
                        mode=opts.camelot_mode,
                        pages=opts.camelot_pages,
                        lattice_accuracy_threshold=opts.camelot_accuracy_threshold
                    )
                else:
                    # Extract tables using Docling (for non-PDF files or when Camelot unavailable)
                    table_extractions, table_summary = extract_tables_from_document(
                        docling_doc,
                        doc_output_dir,
                        doc_name,
                        opts.table_complexity_threshold,
                        assume_header=opts.assume_first_row_header
                    )
            except Exception as e:
                logger.error(f"Error during table extraction: {str(e)}", exc_info=True)
                # Continue without table extraction
                table_extractions = []
                table_summary = {"error": str(e)}

            # Integrate tables into Markdown content
            if opts.output_format == "markdown" and table_extractions and will_use_camelot:
                try:
                    # Replace Docling tables with Camelot tables (high accuracy)
                    content = integrate_camelot_tables_into_content(content, table_extractions, docling_doc)
                except Exception as e:
                    logger.error(f"Error integrating Camelot tables: {str(e)}", exc_info=True)
                    # Continue without table integration

            # Save to output folder structure
            content_path = doc_output_dir / "content.md"
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(content)

            output_structure = {
                "output_dir": str(doc_output_dir),
                "content_file": str(content_path),
                "tables_dir": str(doc_output_dir / "tables") if table_summary and table_summary.get("json_tables", 0) > 0 else None
            }

            output_path = content_path
        elif output_path is None:
            # Legacy mode: save to docu folder (only if not already saved)
            # Determine file extension based on output format
            if opts.output_format == "html":
                ext = ".html"
            elif opts.output_format == "json":
                ext = ".json"
            else:
                ext = ".md"

            output_path = DOCU_FOLDER / f"{file_path.stem}{ext}"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Calculate statistics
        lines = content.count('\n') + 1
        words = len(content.split())
        chars = len(content)

        logger.info(f"✅ Parsing complete: {lines} lines, {words} words, {round(chars / 1024, 2)} KB")

        # Update Document record in database (status=completed)
        if db_document:
            try:
                duration_seconds = time.time() - start_time

                # Update document metadata
                doc_update = schemas.DocumentUpdate(
                    parsing_status="completed",
                    parsing_strategy=strategy,
                    last_parsed_at=datetime.utcnow()
                )

                if output_structure:
                    doc_update.output_folder = output_structure["output_dir"]
                    doc_update.content_md_path = output_structure["content_file"]

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
                                parsing_method="camelot" if will_use_camelot else "docling"
                            )
                            table_creates.append(table_create)

                        if table_creates:
                            crud.create_tables_bulk(db, table_creates)
                            logger.info(f"  💾 Saved {len(table_creates)} tables to database")
                    except Exception as e:
                        logger.error(f"Error saving table metadata: {str(e)}", exc_info=True)

                # Create ParsingHistory record
                try:
                    history_create = schemas.ParsingHistoryCreate(
                        document_id=db_document.id,
                        parsing_status="completed",
                        parsing_strategy=strategy,
                        options_json=json.dumps(opts.model_dump()),
                        total_tables=table_summary.get("total_tables", 0) if table_summary else 0,
                        markdown_tables=table_summary.get("markdown_tables", 0) if table_summary else 0,
                        json_tables=table_summary.get("json_tables", 0) if table_summary else 0,
                        duration_seconds=duration_seconds
                    )
                    crud.create_parsing_history(db, history_create)
                    logger.info(f"  💾 Created parsing history record (duration: {duration_seconds:.2f}s)")
                except Exception as e:
                    logger.error(f"Error creating parsing history: {str(e)}", exc_info=True)
            except Exception as e:
                logger.error(f"Error updating database after parsing: {str(e)}", exc_info=True)

        # Smart Image Analysis: Filter VLM descriptions based on image classification
        if opts.auto_image_analysis and docling_doc:
            try:
                docling_doc = filter_picture_descriptions_smart(docling_doc, auto_mode=True)
            except Exception as e:
                logger.error(f"Error filtering picture descriptions: {str(e)}", exc_info=True)

        # Extract picture information if picture description or auto_image_analysis was enabled
        pictures_summary = None
        if (opts.do_picture_description or opts.auto_image_analysis) and docling_doc:
            try:
                # Include classification info if auto_image_analysis is enabled
                pictures_summary = extract_pictures_info(
                    docling_doc,
                    include_classification=opts.auto_image_analysis
                )
                if pictures_summary["total_pictures"] > 0:
                    if opts.auto_image_analysis and "classification_stats" in pictures_summary:
                        stats = pictures_summary["classification_stats"]
                        logger.info(
                            f"  Pictures: {pictures_summary['total_pictures']} total, "
                            f"{pictures_summary['pictures_with_descriptions']} with VLM descriptions"
                        )
                        logger.info(
                            f"    Classification: {stats['text']} text, {stats['visualization']} viz, "
                            f"{stats['mixed']} mixed, {stats['unknown']} unknown"
                        )
                    else:
                        logger.info(
                            f"  Pictures: {pictures_summary['total_pictures']} total, "
                            f"{pictures_summary['pictures_with_descriptions']} with descriptions"
                        )
            except Exception as e:
                logger.error(f"Error extracting picture info: {str(e)}", exc_info=True)

        # Save parsing metadata to JSON file for later retrieval
        if 'parsing_metadata' in locals() and parsing_metadata and 'doc_output_dir' in locals():
            try:
                metadata_file = doc_output_dir / "metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(parsing_metadata.model_dump(), f, indent=2, ensure_ascii=False)
                logger.info(f"💾 Saved parsing metadata to {metadata_file}")
            except Exception as e:
                logger.error(f"Error saving metadata.json: {str(e)}", exc_info=True)

        return ParseResponse(
            success=True,
            filename=request.filename,
            markdown=content,
            stats={
                "lines": lines,
                "words": words,
                "characters": chars,
                "size_kb": round(chars / 1024, 2)
            },
            saved_to=str(output_path),
            output_format=opts.output_format,
            table_summary=table_summary,
            output_structure=output_structure,
            pictures_summary=pictures_summary,
            warnings=warnings if warnings else None,
            parsing_metadata=parsing_metadata if 'parsing_metadata' in locals() else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing document: {str(e)}", exc_info=True)

        # Update Document record to failed status
        if db_document:
            try:
                duration_seconds = time.time() - start_time

                # Update document status to failed
                crud.update_document(db, db_document.id, schemas.DocumentUpdate(
                    parsing_status="failed",
                    last_parsed_at=datetime.utcnow()
                ))

                # Create ParsingHistory record with error
                history_create = schemas.ParsingHistoryCreate(
                    document_id=db_document.id,
                    parsing_status="failed",
                    parsing_strategy=strategy if 'strategy' in locals() else None,
                    options_json=json.dumps(request.get_options().model_dump()),
                    error_message=str(e),
                    duration_seconds=duration_seconds
                )
                crud.create_parsing_history(db, history_create)
                logger.info(f"  💾 Updated document to failed status and created error history")
            except Exception as db_error:
                logger.error(f"Error updating database after parsing failure: {str(db_error)}", exc_info=True)

        return ParseResponse(
            success=False,
            filename=request.filename,
            error=str(e)
        )
