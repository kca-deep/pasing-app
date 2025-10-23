// API Type Definitions for Document Parsing Application

export interface DocumentInfo {
  filename: string;
  size: number;
  extension: string;
}

export interface ParseOptions {
  // Parsing Strategy
  use_mineru?: boolean;  // Use MinerU (Universal PDF parser)
  use_camelot?: boolean; // Use Camelot for table extraction

  // General options
  do_ocr?: boolean;
  output_format?: 'markdown' | 'html' | 'json';
  extract_tables?: boolean;
  save_to_output_folder?: boolean;

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
