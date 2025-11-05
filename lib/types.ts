// API Type Definitions for Document Parsing Application

export interface DocumentInfo {
  filename: string;
  size: number;
  extension: string;
}

export interface ParseOptions {
  // Parsing Strategy
  use_mineru?: boolean;   // Use MinerU (Universal PDF parser)
  use_camelot?: boolean;  // Use Camelot for table extraction
  use_remote_ocr?: boolean;  // Use Remote OCR service

  // General options
  do_ocr?: boolean;
  ocr_engine?: 'easyocr' | 'tesseract';  // Local OCR engine for Docling
  table_mode?: 'fast' | 'accurate';  // Table extraction accuracy
  output_format?: 'markdown' | 'html' | 'json';
  extract_tables?: boolean;
  save_to_output_folder?: boolean;
  tables_as_html?: boolean;  // Export tables as HTML format
  do_cell_matching?: boolean;  // Enable Docling cell matching

  // Remote OCR options
  remote_ocr_engine?: 'tesseract' | 'paddleocr';
  remote_ocr_languages?: string[];

  // Camelot options (PDF only)
  camelot_mode?: 'lattice' | 'stream' | 'hybrid';
  camelot_pages?: string;
  camelot_accuracy_threshold?: number;

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
  parser_used: string;  // "docling", "mineru", "camelot", "remote_ocr"
  table_parser?: string;  // "docling", "camelot", "mineru"
  ocr_enabled: boolean;
  ocr_engine?: string;  // "easyocr", "remote-tesseract", "remote-paddleocr"
  output_format: string;

  // Parser-specific options used
  camelot_mode?: string;  // "lattice", "stream", "hybrid"
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

// Dify Integration Types
export interface DifyConfig {
  api_key: string
  base_url: string
}

export interface DifyDataset {
  id: string
  name: string
  description?: string
  document_count: number
  word_count: number
  created_at: string
}

export interface ParsedDocument {
  // File info (for Dify upload)
  path: string
  name: string
  size: number
  created_at: string

  // Database metadata
  id?: number
  filename?: string
  file_extension?: string
  file_size?: number  // Original file size in bytes
  total_pages?: number
  parsing_status?: string
  parsing_strategy?: string
  last_parsed_at?: string  // ISO 8601 format

  // Aggregated counts
  chunk_count: number
  table_count: number
  picture_count: number
}

export interface UploadRequest {
  dataset_id: string
  document_path: string
  document_name?: string
  indexing_technique?: string
}

export interface UploadResponse {
  document_id: string
  batch_id: string
  indexing_status: 'waiting' | 'indexing' | 'completed' | 'error'
  success: boolean
}

export interface IndexingStatus {
  id: string
  indexing_status: 'waiting' | 'indexing' | 'completed' | 'error'
  completed_segments: number
  total_segments: number
  processing_started_at?: string
  completed_at?: string
  error?: string
}

export interface DifyUploadLog {
  id: number
  dataset_id: string
  dataset_name: string
  document_name: string
  indexing_status: string
  uploaded_at: string
  completed_at?: string
}

export interface DocumentUploadStatus {
  path: string
  name: string
  status: 'waiting' | 'uploading' | 'completed' | 'error'
  progress: number
  error?: string
  document_id?: string
}
