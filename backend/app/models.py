"""
Pydantic models for request and response schemas.
"""

from pydantic import BaseModel
from typing import List, Optional, Literal


# Pydantic models
class TableParsingOptions(BaseModel):
    """Table parsing options"""
    # Basic parsing options
    do_ocr: bool = False  # OCR for scanned PDFs (default: False for speed)
    table_mode: str = "accurate"  # Table detection mode: "fast" or "accurate"
    do_cell_matching: bool = False  # False: more effective for merged cells
    ocr_lang: Optional[List[str]] = None  # OCR languages, e.g., ["ko", "en"]

    # Output format options
    output_format: Literal["markdown", "html", "json"] = "markdown"  # Output format (HTML supports merged cells)

    # Phase 2.1: Markdown export optimization (based on Docling export_to_markdown parameters)
    escape_html: bool = False  # False: Allow HTML tags in Markdown (for structure preservation)
    strict_text: bool = False  # True: Pure text only (no Markdown formatting)
    image_mode: Literal["placeholder", "embedded", "referenced"] = "placeholder"  # Image reference mode
    enable_chart_tables: bool = True  # Enable chart table processing
    image_placeholder: str = "<!-- image -->"  # Placeholder text for images
    indent: int = 4  # Indentation level for nested structures

    # Phase 2.2: Custom serialization (표만 HTML, 나머지 Markdown)
    tables_as_html: bool = False  # False: Export tables as Markdown (default for Camelot compatibility)

    # Phase 3: RAG optimization options
    extract_tables: bool = True  # Extract tables separately
    table_complexity_threshold: int = 4  # Size threshold for complex tables (default: 4x4)
    save_to_output_folder: bool = True  # Save to output/{doc_name}/ structure

    # Table structure parsing options (flexible, no hardcoding)
    assume_first_row_header: Optional[bool] = None  # None = auto-detect, True/False = force

    # Camelot table extraction options (PDF only, high accuracy)
    # NOTE: Camelot is automatically used for PDF files (default behavior)
    # For non-PDF files (DOCX, PPTX, HTML), Docling is used automatically
    use_camelot: bool = True  # Use Camelot for table extraction (default: True for PDFs)
    camelot_mode: Literal["lattice", "stream", "hybrid"] = "hybrid"  # Camelot extraction mode
    camelot_pages: str = "all"  # Pages to extract tables from (e.g., "1,2,3" or "1-5" or "all")
    camelot_accuracy_threshold: float = 0.7  # Minimum accuracy for LATTICE mode (0.0-1.0)

    # MinerU options (Universal PDF parser, 문서 타입 독립적)
    # NOTE: MinerU는 모든 문서 타입을 자동으로 처리 (하드코딩 불필요)
    # Features: 병합 셀, 계층적 표, 텍스트 순서 자동 정렬, 84개 언어 지원
    use_mineru: bool = False  # Use MinerU for parsing (recommended for complex documents)
    mineru_lang: Literal["auto", "ko", "ch", "en", "ja"] = "auto"  # Language (auto = automatic detection)
    mineru_use_ocr: bool = True  # Use OCR for scanned documents

    # Picture Description options (Vision Language Model for image analysis)
    do_picture_description: bool = False  # Enable picture description (default: False for performance)
    picture_description_model: Literal["smolvlm", "granite", "custom"] = "smolvlm"  # VLM model choice
    picture_description_prompt: str = "Describe this image in a few sentences. Be precise and concise."  # Custom prompt
    picture_area_threshold: float = 0.05  # Minimum picture area threshold (0.0-1.0)
    picture_images_scale: float = 2.0  # Image scaling factor for better quality
    custom_vlm_repo_id: Optional[str] = None  # Custom Hugging Face VLM repo ID (for "custom" model)

    # Smart Image Processing (Auto-select OCR vs Picture Description)
    auto_image_analysis: bool = False  # Enable automatic image type detection and processing
    # When enabled:
    #   - Text-heavy images (tables, forms) → OCR only
    #   - Visualizations (charts, graphs, diagrams) → Picture Description
    #   - Complex images → Both OCR + Picture Description


class ParseRequest(BaseModel):
    filename: str
    options: Optional[TableParsingOptions] = None

    def get_options(self) -> TableParsingOptions:
        """Return default options"""
        return self.options or TableParsingOptions()


class DocumentInfo(BaseModel):
    filename: str
    size: int
    extension: str


class ParseResponse(BaseModel):
    success: bool
    filename: str
    markdown: Optional[str] = None  # Output content (Markdown, HTML, or JSON)
    stats: Optional[dict] = None
    saved_to: Optional[str] = None
    error: Optional[str] = None
    output_format: Optional[str] = None  # Actual output format

    # Phase 3: Table extraction results
    table_summary: Optional[dict] = None  # Summary of extracted tables
    output_structure: Optional[dict] = None  # File structure in output folder

    # Picture Description results
    pictures_summary: Optional[dict] = None  # Summary of pictures with descriptions

    # Warnings for user (e.g., MinerU requested but not installed)
    warnings: Optional[List[str]] = None
