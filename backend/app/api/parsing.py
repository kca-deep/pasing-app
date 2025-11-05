"""
Document parsing endpoints.

Main parsing logic that orchestrates Docling, Camelot, and VLM processing.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import DOCU_FOLDER, OUTPUT_FOLDER
from app.database import get_db
from app.models import ParseRequest, ParseResponse, ParsingMetadata
from app.services.docling import parse_document_with_docling
from app.services.mineru_parser import MINERU_AVAILABLE, parse_with_mineru
from app.services.pictures import (
    extract_pictures_info,
    filter_picture_descriptions_smart,
)
from app.services.remote_ocr_parser import REMOTE_OCR_AVAILABLE, parse_with_remote_ocr
from app.services.tables import integrate_camelot_tables_into_content
from app.table_utils import (
    CAMELOT_AVAILABLE,
    extract_tables_from_document,
    extract_tables_with_camelot,
)
from app.utils.file_utils import (
    build_output_structure,
    create_document_output_dir,
    create_versioned_output_dir,
    generate_version_folder_name,
)
from app.utils.parsing_db import (
    create_or_update_document_record,
    save_parsing_failure,
    save_parsing_success,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/parse", response_model=ParseResponse)
async def parse_document(request: ParseRequest, db: Session = Depends(get_db)):
    """Parse document in docu folder to Markdown/HTML/JSON using Docling library"""
    start_time = time.time()

    # Initialize all variables explicitly to avoid locals() anti-pattern
    db_document: Optional[Any] = None
    warnings: List[str] = []
    table_summary: Optional[Dict[str, Any]] = None
    output_structure: Optional[Dict[str, str]] = None
    output_path: Optional[Path] = None
    table_extractions: List[Any] = []
    parsing_metadata: Optional[ParsingMetadata] = None
    docling_doc: Optional[Any] = None
    strategy: str = ""
    will_use_camelot: bool = False
    version_folder: Optional[str] = None  # Version management

    try:
        file_path = DOCU_FOLDER / request.filename

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Create or update Document record in database (status=processing)
        db_document = create_or_update_document_record(db, request.filename, file_path)

        # Get parsing options
        opts = request.get_options()

        # Auto-select parsing strategy based on file type
        is_pdf = file_path.suffix.lower() == ".pdf"

        # 🆕 Remote OCR 사용 (한글 문서 최적화, 스캔된 PDF/이미지)
        if opts.use_remote_ocr and REMOTE_OCR_AVAILABLE:
            strategy = f"Remote OCR ({opts.remote_ocr_engine})"
            logger.info(f"📄 Parsing: {request.filename} | Strategy: {strategy}")

            # Generate version folder name
            version_folder = generate_version_folder_name(
                strategy=strategy,
                options={
                    "remote_ocr_engine": opts.remote_ocr_engine,
                    "remote_ocr_languages": opts.remote_ocr_languages,
                },
            )

            # Create versioned output directory
            doc_output_dir = create_versioned_output_dir(
                file_path=file_path, base_dir=OUTPUT_FOLDER, version_folder=version_folder
            )

            # Remote OCR로 파싱
            try:
                ocr_langs = opts.remote_ocr_languages or ["kor", "eng"]
                content, remote_ocr_metadata = parse_with_remote_ocr(
                    file_path,
                    ocr_engine=opts.remote_ocr_engine,
                    ocr_languages=ocr_langs,
                    output_dir=doc_output_dir if opts.save_to_output_folder else None,
                )

                # 메타데이터 변환
                table_summary = {
                    "parsing_method": "remote_ocr",
                    "ocr_engine": opts.remote_ocr_engine,
                    "ocr_languages": ocr_langs,
                    "total_pages": remote_ocr_metadata.get("pages", 1),
                    "total_characters": remote_ocr_metadata.get(
                        "characters_extracted", 0
                    ),
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
                    auto_image_analysis_enabled=False,
                )

                # output_structure 설정
                output_structure = build_output_structure(
                    doc_output_dir, has_tables=False, has_images=False
                ).to_dict()
                output_path = Path(output_structure["content_file"])

                logger.info(
                    f"✅ Remote OCR parsing completed ({opts.remote_ocr_engine})"
                )

            except Exception as e:
                logger.error(
                    f"Error during Remote OCR parsing: {str(e)}", exc_info=True
                )
                raise HTTPException(
                    status_code=500, detail=f"Remote OCR parsing failed: {str(e)}"
                )

        elif opts.use_remote_ocr and not REMOTE_OCR_AVAILABLE:
            # Remote OCR 요청했지만 서버 연결 안 됨 → 경고 후 fallback
            warnings.append(
                "Remote OCR Server not available. Falling back to Docling with EasyOCR."
            )
            logger.warning(
                "⚠️ Remote OCR requested but server not available, falling back to Docling"
            )
            # Continue to next strategy (Dolphin or Docling)

        # 🆕 MinerU 우선 사용 (범용 솔루션)
        elif is_pdf and opts.use_mineru and MINERU_AVAILABLE:
            strategy = "MinerU (Universal)"
            logger.info(f"📄 Parsing: {request.filename} | Strategy: {strategy}")

            # Generate version folder name
            version_folder = generate_version_folder_name(strategy=strategy)

            # Create versioned output directory
            doc_output_dir = create_versioned_output_dir(
                file_path=file_path, base_dir=OUTPUT_FOLDER, version_folder=version_folder
            )

            # MinerU로 파싱 (로컬 라이브러리)
            try:
                content, mineru_metadata = parse_with_mineru(
                    file_path,
                    output_dir=doc_output_dir,
                    output_format=opts.output_format,
                    lang=opts.mineru_lang,
                    use_ocr=opts.mineru_use_ocr,
                    progress_callback=None,  # No progress tracking in sync mode
                )

                # MinerU는 자체적으로 표를 처리하므로 table_summary는 MinerU 메타데이터 사용
                table_summary = {
                    "total_tables": mineru_metadata.get("tables", 0),
                    "total_images": mineru_metadata.get("images", 0),
                    "total_formulas": mineru_metadata.get("formulas", 0),
                    "parsing_method": "mineru",
                    "language": mineru_metadata.get("language"),
                    "ocr_enabled": mineru_metadata.get("ocr_enabled", False),
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
                    auto_image_analysis_enabled=False,
                )

                # MinerU는 자체적으로 content.md를 생성하므로 output_structure 설정
                output_structure = build_output_structure(
                    doc_output_dir, has_tables=False, has_images=True
                ).to_dict()
                output_path = Path(output_structure["content_file"])

            except Exception as e:
                logger.error(f"Error during MinerU parsing: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500, detail=f"MinerU parsing failed: {str(e)}"
                )

        elif is_pdf and opts.use_mineru and not MINERU_AVAILABLE:
            # MinerU 요청했지만 설치 안 됨 → 에러 반환 (fallback 없음)
            error_msg = (
                "MinerU is not installed. Please install MinerU to use this feature.\n\n"
                "Installation command:\n"
                "  pip install magic-pdf[full]\n\n"
                "Or use Camelot/Docling parsing strategy instead."
            )
            logger.error("MinerU requested but not available")
            raise HTTPException(status_code=400, detail=error_msg)

        else:
            # 기존 Camelot/Docling 로직 (MinerU 미사용)
            will_use_camelot = opts.use_camelot and is_pdf and CAMELOT_AVAILABLE

            if is_pdf and opts.use_camelot and not CAMELOT_AVAILABLE:
                logger.warning(
                    "⚠️ Camelot requested but not available. Falling back to Docling."
                )

            strategy = "Docling+Camelot Hybrid" if will_use_camelot else "Docling Only"
            logger.info(f"📄 Parsing: {request.filename} | Strategy: {strategy}")

            # Generate version folder name
            version_folder = generate_version_folder_name(
                strategy=strategy,
                options={
                    "camelot_mode": opts.camelot_mode if will_use_camelot else None,
                    "ocr_engine": opts.ocr_engine if opts.do_ocr else None,
                    "ocr_lang": opts.ocr_lang if opts.do_ocr else None,
                },
            )

            # Force Markdown table export when using Camelot (for compatibility)
            if will_use_camelot and opts.tables_as_html:
                logger.info("  Forcing tables_as_html=False for Camelot compatibility")

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
                auto_image_analysis_enabled=opts.auto_image_analysis,
            )

        # Phase 3: Extract tables if enabled
        # NOTE: MinerU 사용 시 table_summary와 output_structure가 이미 설정되어 있음

        # MinerU를 사용한 경우 table extraction 스킵 (MinerU가 자동 처리)
        if (
            opts.extract_tables
            and opts.save_to_output_folder
            and docling_doc
            and output_structure is None
        ):
            try:
                # Create versioned output directory
                doc_output_dir = create_versioned_output_dir(
                    file_path=file_path,
                    base_dir=OUTPUT_FOLDER,
                    version_folder=version_folder,
                )
                doc_name = file_path.stem

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
                        lattice_accuracy_threshold=opts.camelot_accuracy_threshold,
                    )
                else:
                    # Extract tables using Docling (for non-PDF files or when Camelot unavailable)
                    table_extractions, table_summary = extract_tables_from_document(
                        docling_doc,
                        doc_output_dir,
                        doc_name,
                        opts.table_complexity_threshold,
                        assume_header=opts.assume_first_row_header,
                    )
            except Exception as e:
                logger.error(f"Error during table extraction: {str(e)}", exc_info=True)
                # Continue without table extraction
                table_extractions = []
                table_summary = {"error": str(e)}

            # Integrate tables into Markdown content
            if (
                opts.output_format == "markdown"
                and table_extractions
                and will_use_camelot
            ):
                try:
                    # Replace Docling tables with Camelot tables (high accuracy)
                    content = integrate_camelot_tables_into_content(
                        content, table_extractions, docling_doc
                    )
                except Exception as e:
                    logger.error(
                        f"Error integrating Camelot tables: {str(e)}", exc_info=True
                    )
                    # Continue without table integration

            # Save to output folder structure
            has_tables = bool(table_summary and table_summary.get("json_tables", 0) > 0)
            output_structure = build_output_structure(
                doc_output_dir, has_tables=has_tables, has_images=False
            ).to_dict()

            content_path = Path(output_structure["content_file"])
            with open(content_path, "w", encoding="utf-8") as f:
                f.write(content)

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
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Calculate statistics
        lines = content.count("\n") + 1
        words = len(content.split())
        chars = len(content)

        logger.info(
            f"✅ Parsing complete: {lines} lines, {words} words, {round(chars / 1024, 2)} KB"
        )

        # Save to database
        duration_seconds = time.time() - start_time
        save_parsing_success(
            db=db,
            db_document=db_document,
            strategy=strategy,
            output_structure=output_structure,
            duration_seconds=duration_seconds,
            options=opts,
            version_folder=version_folder,
            table_summary=table_summary,
            table_extractions=table_extractions if table_extractions else None,
            parsing_method="camelot" if will_use_camelot else "docling",
        )

        # Smart Image Analysis: Filter VLM descriptions based on image classification
        if opts.auto_image_analysis and docling_doc:
            try:
                docling_doc = filter_picture_descriptions_smart(
                    docling_doc, auto_mode=True
                )
            except Exception as e:
                logger.error(
                    f"Error filtering picture descriptions: {str(e)}", exc_info=True
                )

        # Extract picture information if picture description or auto_image_analysis was enabled
        pictures_summary = None
        if (opts.do_picture_description or opts.auto_image_analysis) and docling_doc:
            try:
                # Include classification info if auto_image_analysis is enabled
                pictures_summary = extract_pictures_info(
                    docling_doc, include_classification=opts.auto_image_analysis
                )
                if pictures_summary["total_pictures"] > 0:
                    if (
                        opts.auto_image_analysis
                        and "classification_stats" in pictures_summary
                    ):
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
        if parsing_metadata is not None and output_structure is not None:
            try:
                doc_output_dir = Path(output_structure["output_dir"])
                metadata_file = doc_output_dir / "metadata.json"
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(
                        parsing_metadata.model_dump(), f, indent=2, ensure_ascii=False
                    )
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
                "size_kb": round(chars / 1024, 2),
            },
            saved_to=str(output_path),
            output_format=opts.output_format,
            table_summary=table_summary,
            output_structure=output_structure,
            pictures_summary=pictures_summary,
            warnings=warnings if warnings else None,
            parsing_metadata=parsing_metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing document: {str(e)}", exc_info=True)

        # Save failure to database
        duration_seconds = time.time() - start_time
        save_parsing_failure(
            db=db,
            db_document=db_document,
            strategy=strategy if strategy else None,
            error_message=str(e),
            duration_seconds=duration_seconds,
            options=request.get_options(),
            version_folder=version_folder,
        )

        return ParseResponse(success=False, filename=request.filename, error=str(e))
