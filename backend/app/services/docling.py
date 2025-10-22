"""
Docling parsing service.

Handles document parsing using the Docling library.
"""

from pathlib import Path
import json
import logging

# Docling imports for direct library usage
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    PictureDescriptionVlmOptions,
    smolvlm_picture_description,
    granite_picture_description
)
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling_core.types.doc import ImageRefMode

# Import custom serializers for mixed Markdown+HTML output
from app.custom_serializers import HTMLTableSerializer
from app.models import TableParsingOptions

logger = logging.getLogger(__name__)


async def parse_document_with_docling(file_path: Path, opts: TableParsingOptions) -> tuple:
    """
    Parse document using Docling library directly (Standard PDF Pipeline only)

    Returns:
        Tuple of (content_string, docling_document)
        - content_string: Exported content (Markdown/HTML/JSON)
        - docling_document: DoclingDocument object for Phase 3+ table extraction

    Note:
        Always parses tables with Docling to identify table locations.
        When use_camelot=True, Camelot tables will replace Docling tables in the final output.

        Picture Description is applied only when enabled and only to images above area threshold.
    """
    # Standard PDF Pipeline (Fast and accurate)
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = opts.do_ocr

    # Korean language optimization for OCR (EasyOCR)
    if opts.do_ocr:
        pipeline_options.ocr_options.lang = ["ko", "en"]  # Korean + English
        logger.info("  OCR: Korean + English language support enabled")

    pipeline_options.do_table_structure = True

    # Table mode: FAST or ACCURATE
    if opts.table_mode == "fast":
        pipeline_options.table_structure_options.mode = TableFormerMode.FAST
    else:
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    pipeline_options.table_structure_options.do_cell_matching = opts.do_cell_matching

    # Smart Image Analysis: Auto-detect image type and apply appropriate processing
    if opts.auto_image_analysis:
        logger.info("  Smart Image Analysis: Enabled (auto-selecting OCR vs VLM)")

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

        logger.info("    - OCR: Enabled (text extraction)")
        logger.info("    - Classification: Enabled (image type detection)")
        logger.info("    - VLM: Enabled (visualization description)")

    # Manual Picture Description configuration (only when enabled and auto_image_analysis is off)
    elif opts.do_picture_description:
        logger.info(f"  Picture Description: Enabled (model={opts.picture_description_model}, threshold={opts.picture_area_threshold})")

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
            logger.warning(f"  Invalid model or missing repo_id, falling back to SmolVLM")
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

    # Convert document
    result = converter.convert(file_path)
    docling_doc = result.document

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

    return content, docling_doc
