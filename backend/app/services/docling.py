"""
Docling parsing service.

Handles document parsing using the Docling library.
"""

from pathlib import Path
from typing import Optional, Tuple, Any
import json
import logging
import os

# Docling imports for direct library usage
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    PictureDescriptionVlmOptions,
    TesseractOcrOptions,
    EasyOcrOptions,
    smolvlm_picture_description,
    granite_picture_description
)
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling_core.types.doc import ImageRefMode

# Import custom serializers for mixed Markdown+HTML output
from app.custom_serializers import HTMLTableSerializer
from app.models import TableParsingOptions

logger = logging.getLogger(__name__)

# Import standardized logging utility
from app.utils.logging_utils import ParserLogger

# Docling EasyOCR 기본 언어 설정
DEFAULT_DOCLING_OCR_LANGUAGES = os.getenv("DEFAULT_DOCLING_OCR_LANGUAGES", "ko,en").split(",")

# OCR engine availability
EASYOCR_AVAILABLE = True  # EasyOCR is always available in Docling
logger.info("✅ [EasyOCR] Available (default OCR engine)")


def parse_document_with_docling(
    file_path: Path,
    opts: TableParsingOptions,
    progress_callback: Optional[callable] = None
) -> Tuple[str, Any]:
    """
    Parse document using Docling library directly (Standard PDF Pipeline only)

    Args:
        file_path: Path to document file
        opts: Table parsing options
        progress_callback: Optional callback function(percent, message) for progress tracking

    Returns:
        Tuple of (content_string, docling_document)
        - content_string: Exported content (Markdown/HTML/JSON)
        - docling_document: DoclingDocument object for Phase 3+ table extraction

    Note:
        Always parses tables with Docling to identify table locations.
        When use_camelot=True, Camelot tables will replace Docling tables in the final output.

        Picture Description is applied only when enabled and only to images above area threshold.
    """
    # Initialize standardized logger
    parser_logger = ParserLogger("Docling", logger)

    # Log parser start with configuration
    parser_logger.start(
        file_path.name,
        output_format=opts.output_format,
        do_ocr=opts.do_ocr,
        ocr_engine=opts.ocr_engine if opts.do_ocr else "N/A",
        table_mode=opts.table_mode,
        extract_tables=opts.extract_tables if hasattr(opts, 'extract_tables') else False,
        auto_image_analysis=opts.auto_image_analysis if opts.auto_image_analysis else False,
        do_picture_description=opts.do_picture_description if opts.do_picture_description else False,
        tables_as_html=opts.tables_as_html if hasattr(opts, 'tables_as_html') else False,
        do_cell_matching=opts.do_cell_matching
    )

    # Standard PDF Pipeline (Fast and accurate)
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = opts.do_ocr

    # OCR Configuration
    if opts.do_ocr:
        # Remote OCR 요청은 Docling에서 처리 불가
        # Remote OCR는 parsing.py에서 parse_with_remote_ocr()로 별도 처리됨
        if opts.use_remote_ocr:
            # Docling은 remote OCR을 지원하지 않으므로 local OCR로 fallback
            parser_logger.warning(
                "Docling does not support remote OCR. Using local OCR instead.",
                suggestion="Set use_remote_ocr=True at the parsing.py level"
            )

            ocr_langs = opts.ocr_lang or opts.remote_ocr_languages or DEFAULT_DOCLING_OCR_LANGUAGES

            # Always use EasyOCR (built-in, no installation needed)
            pipeline_options.ocr_options = EasyOcrOptions(lang=ocr_langs)
        else:
            # Local OCR - always use EasyOCR
            ocr_langs = opts.ocr_lang or DEFAULT_DOCLING_OCR_LANGUAGES
            pipeline_options.ocr_options = EasyOcrOptions(lang=ocr_langs)

    pipeline_options.do_table_structure = True

    # Table mode: FAST or ACCURATE
    if opts.table_mode == "fast":
        pipeline_options.table_structure_options.mode = TableFormerMode.FAST
    else:
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    pipeline_options.table_structure_options.do_cell_matching = opts.do_cell_matching

    # Progress: Pipeline configured
    if progress_callback:
        progress_callback(10, "Pipeline configured...")

    # Smart Image Analysis: Auto-detect image type and apply appropriate processing
    if opts.auto_image_analysis:
        # Enable all image processing features
        pipeline_options.do_ocr = True  # Extract text from images
        pipeline_options.do_picture_classification = True  # Classify image types
        pipeline_options.do_picture_description = True  # Generate descriptions for visualizations
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = opts.picture_images_scale

        # Configure VLM
        if opts.picture_description_model == "smolvlm":
            pipeline_options.picture_description_options = smolvlm_picture_description
        elif opts.picture_description_model == "granite":
            pipeline_options.picture_description_options = granite_picture_description
        elif opts.picture_description_model == "custom" and opts.custom_vlm_repo_id:
            pipeline_options.picture_description_options = PictureDescriptionVlmOptions(
                repo_id=opts.custom_vlm_repo_id,
                prompt=opts.picture_description_prompt,
                picture_area_threshold=opts.picture_area_threshold,
                scale=opts.picture_images_scale
            )
        else:
            pipeline_options.picture_description_options = smolvlm_picture_description

        pipeline_options.picture_description_options.prompt = opts.picture_description_prompt
        pipeline_options.picture_description_options.picture_area_threshold = opts.picture_area_threshold

    # Manual Picture Description configuration (only when enabled and auto_image_analysis is off)
    elif opts.do_picture_description:
        pipeline_options.do_picture_description = True
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = opts.picture_images_scale

        # Select VLM model
        if opts.picture_description_model == "smolvlm":
            pipeline_options.picture_description_options = smolvlm_picture_description
        elif opts.picture_description_model == "granite":
            pipeline_options.picture_description_options = granite_picture_description
        elif opts.picture_description_model == "custom" and opts.custom_vlm_repo_id:
            pipeline_options.picture_description_options = PictureDescriptionVlmOptions(
                repo_id=opts.custom_vlm_repo_id,
                prompt=opts.picture_description_prompt,
                picture_area_threshold=opts.picture_area_threshold,
                scale=opts.picture_images_scale
            )
        else:
            # Default to SmolVLM
            parser_logger.warning(
                "Invalid VLM model or missing repo_id, falling back to SmolVLM",
                model=opts.picture_description_model
            )
            pipeline_options.picture_description_options = smolvlm_picture_description

        # Apply custom settings
        pipeline_options.picture_description_options.prompt = opts.picture_description_prompt
        pipeline_options.picture_description_options.picture_area_threshold = opts.picture_area_threshold

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=StandardPdfPipeline,
                pipeline_options=pipeline_options
            )
        }
    )

    # Progress: Converter created
    if progress_callback:
        progress_callback(20, "Converter initialized...")

    # Progress: Starting document conversion
    if progress_callback:
        progress_callback(30, "Converting document...")

    # Convert document
    result = converter.convert(file_path)
    docling_doc = result.document

    # Progress: Document converted
    if progress_callback:
        progress_callback(80, "Document converted successfully...")

    # Progress: Exporting content
    if progress_callback:
        progress_callback(90, "Exporting content...")

    # Export based on output format
    if opts.output_format == "html":
        # HTML supports colspan/rowspan for merged cells
        content = docling_doc.export_to_html()
    elif opts.output_format == "json":
        # JSON includes RichTableCell's row_span, col_span metadata
        content = json.dumps(docling_doc.export_to_dict(), ensure_ascii=False, indent=2)
    else:  # markdown (default)

        # Phase 2.2: Use custom serializer for mixed Markdown + HTML output
        if opts.tables_as_html:
            # Use MarkdownDocSerializer with HTMLTableSerializer for tables
            from docling_core.transforms.serializer.markdown import MarkdownDocSerializer, MarkdownParams

            # Map string image_mode to ImageRefMode enum
            image_mode_map = {
                "placeholder": ImageRefMode.PLACEHOLDER,
                "embedded": ImageRefMode.EMBEDDED,
                "referenced": ImageRefMode.REFERENCED
            }
            image_mode_enum = image_mode_map.get(opts.image_mode, ImageRefMode.PLACEHOLDER)

            # Create MarkdownParams
            markdown_params = MarkdownParams(
                escape_html=opts.escape_html,            # False: Allow HTML tags
                image_mode=image_mode_enum,              # Image reference mode
                image_placeholder=opts.image_placeholder, # Custom image placeholder
                indent=opts.indent                       # Indentation level
            )

            # Create serializer with HTMLTableSerializer
            serializer = MarkdownDocSerializer(
                doc=docling_doc,
                table_serializer=HTMLTableSerializer(),  # Tables as HTML
                params=markdown_params
            )

            # Serialize document
            ser_result = serializer.serialize()
            content = ser_result.text
        else:
            # Phase 2.1: Standard Markdown export (all Markdown, no HTML tables)
            # Map string image_mode to ImageRefMode enum
            image_mode_map = {
                "placeholder": ImageRefMode.PLACEHOLDER,
                "embedded": ImageRefMode.EMBEDDED,
                "referenced": ImageRefMode.REFERENCED
            }
            image_mode_enum = image_mode_map.get(opts.image_mode, ImageRefMode.PLACEHOLDER)

            # Call export_to_markdown with optimized parameters for RAG
            content = docling_doc.export_to_markdown(
                strict_text=opts.strict_text,           # False: Keep Markdown formatting (headings, lists, etc.)
                escape_html=opts.escape_html,           # False: Allow HTML tags for structure preservation
                image_mode=image_mode_enum,             # Image reference mode (placeholder/embedded/referenced)
                enable_chart_tables=opts.enable_chart_tables,  # Enable chart table processing
                image_placeholder=opts.image_placeholder,      # Custom image placeholder
                indent=opts.indent                      # Indentation level for nested structures
            )

    # Log successful completion with metrics
    num_pages = docling_doc.pages if hasattr(docling_doc, 'pages') and docling_doc.pages else 0
    num_tables = len([item for item in docling_doc.main_text if hasattr(item, 'label') and item.label == 'table']) if hasattr(docling_doc, 'main_text') else 0
    content_length = len(content)

    parser_logger.success(
        "Document parsed successfully",
        pages=num_pages if isinstance(num_pages, int) else len(num_pages) if num_pages else "N/A",
        tables=num_tables,
        content_chars=content_length,
        format=opts.output_format
    )

    # Progress: Complete
    if progress_callback:
        progress_callback(100, "Parsing complete")

    return content, docling_doc
