// API Type Definitions for Document Parsing Application

export interface DocumentInfo {
  filename: string;
  size: number;
  extension: string;
}

export interface ParseOptions {
  // Parsing Strategy
  use_dolphin?: boolean;  // Use Dolphin (AI-Powered parser)
  use_mineru?: boolean;   // Use MinerU (Universal PDF parser)
  use_camelot?: boolean;  // Use Camelot for table extraction
  use_remote_ocr?: boolean;  // Use Remote OCR service

  // General options
  do_ocr?: boolean;
  ocr_engine?: 'easyocr' | 'tesseract';  // Local OCR engine for Docling
  output_format?: 'markdown' | 'html' | 'json';
  extract_tables?: boolean;
  save_to_output_folder?: boolean;

  // Remote OCR options
  remote_ocr_engine?: 'tesseract' | 'paddleocr' | 'dolphin';
  remote_ocr_languages?: string[];

  // Camelot options (PDF only)
  camelot_mode?: 'lattice' | 'stream' | 'hybrid';
  camelot_pages?: string;
  camelot_accuracy_threshold?: number;

  // Dolphin options (AI-Powered via Remote GPU)
  dolphin_parsing_level?: 'page' | 'element' | 'layout';
  dolphin_max_batch_size?: number;

  // MinerU options (Universal)
  mineru_lang?: 'auto' | 'ko' | 'zh' | 'en' | 'ja';
  mineru_use_ocr?: boolean;

  // Picture Description options
  do_picture_description?: boolean;
  auto_image_analysis?: boolean;
}

export interface ParseRequest {
  filename: string;
  options?: ParseOptions;
}

export interface ParsingMetadata {
  parser_used: string;  // "docling", "mineru", "dolphin", "camelot", "remote_ocr"
  table_parser?: string;  // "docling", "camelot", "mineru"
  ocr_enabled: boolean;
  ocr_engine?: string;  // "easyocr", "remote-tesseract", "remote-paddleocr", "remote-dolphin"
  output_format: string;

  // Parser-specific options used
  camelot_mode?: string;  // "lattice", "stream", "hybrid"
  dolphin_parsing_level?: string;  // "page", "element", "layout"
  mineru_lang?: string;  // "auto", "ko", "zh", "en", "ja"

  // Additional features used
  picture_description_enabled: boolean;
  auto_image_analysis_enabled: boolean;
}

export interface ParseResponse {
  success: boolean;
  filename: string;
  markdown?: string;
  stats?: {
    lines: number;
    words: number;
    characters: number;
    size_kb: number;
  };
  saved_to?: string;
  error?: string;
  output_format?: string;
  table_summary?: {
    total_tables?: number;
    markdown_tables?: number;
    json_tables?: number;
    json_table_ids?: string[];
  };
  output_structure?: {
    output_dir: string;
    content_file: string;
    tables_dir?: string;
  };
  pictures_summary?: {
    total_pictures: number;
    pictures_with_descriptions: number;
    pictures: any[];
  };
  warnings?: string[];
  parsing_metadata?: ParsingMetadata;  // v2.3.0+
}

export interface TableData {
  table_id: string;
  chunk_id?: string;
  page: number;
  caption?: string;
  complexity: {
    rows: number;
    cols: number;
    has_merged_cells: boolean;
    is_complex: boolean;
  };
  structure: {
    headers: string[][];
    rows: string[][];
  };
  summary?: string;
}
