// API Client for FastAPI Backend

import type {
  DocumentInfo,
  ParseRequest,
  ParseResponse,
  DifyConfig,
  DifyDataset,
  ParsedDocument,
  UploadRequest,
  UploadResponse,
  IndexingStatus,
  DifyUploadLog
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Get API status and version information
 */
export async function getApiStatus() {
  const response = await fetch(`${API_BASE_URL}/`);
  if (!response.ok) {
    throw new Error(`API status check failed: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get list of all documents in the /docu folder
 */
export async function getDocuments(): Promise<DocumentInfo[]> {
  const response = await fetch(`${API_BASE_URL}/documents`);
  if (!response.ok) {
    throw new Error(`Failed to fetch documents: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Upload a file to the backend
 * @param file - File to upload
 * @returns Upload response with filename and size
 */
export async function uploadFile(file: File): Promise<{
  success: boolean;
  filename: string;
  size: number;
  message: string;
}> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
    // Increase timeout for large files
    signal: AbortSignal.timeout(300000), // 5 minutes
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(errorData.detail || errorData.error || `Upload failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Parse a document using the FastAPI backend (synchronous)
 * @param request - Parse request with filename and options
 * @returns Parse response with content and metadata
 */
export async function parseDocument(request: ParseRequest): Promise<ParseResponse> {
  const response = await fetch(`${API_BASE_URL}/parse`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
    // Increase timeout for large files
    signal: AbortSignal.timeout(300000), // 5 minutes
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(errorData.error || `Parsing failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Start asynchronous document parsing job
 * @param request - Parse request with filename and options
 * @returns Job information with job_id
 */
export async function parseDocumentAsync(request: ParseRequest): Promise<{
  success: boolean;
  job_id: string;
  filename: string;
  message: string;
}> {
  const response = await fetch(`${API_BASE_URL}/parse/async`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(errorData.detail || errorData.error || `Failed to start parsing: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get parsing job status and progress
 * @param jobId - Job identifier
 * @returns Job progress information
 */
export async function getParsingStatus(jobId: string): Promise<{
  job_id: string;
  filename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  result: ParseResponse | null;
  error: string | null;
}> {
  const response = await fetch(`${API_BASE_URL}/parse/status/${jobId}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(errorData.detail || errorData.error || `Failed to get status: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get list of all parsed documents
 * @returns List of parsed documents with metadata
 */
export async function getParsedDocuments(): Promise<{
  total: number;
  documents: Array<{
    document_name: string;
    parsed_at: number;
    size_kb: number;
    preview: string;
    table_count: number;
    output_dir: string;
    parsing_metadata?: {
      parser_used: string;
      table_parser?: string;
      ocr_enabled: boolean;
      ocr_engine?: string;
      output_format: string;
      camelot_mode?: string;
      dolphin_parsing_level?: string;
      mineru_lang?: string;
      picture_description_enabled: boolean;
      auto_image_analysis_enabled: boolean;
    };
  }>;
}> {
  const response = await fetch(`${API_BASE_URL}/parsed-documents`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(errorData.detail || errorData.error || `Failed to get parsed documents: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get parsing result for a previously parsed document
 * @param filename - Name of the document file
 * @returns Parse response with content and metadata
 */
export async function getParseResult(filename: string): Promise<ParseResponse> {
  const response = await fetch(`${API_BASE_URL}/result/${encodeURIComponent(filename)}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(errorData.detail || errorData.error || `Failed to get result: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Download a converted file from the backend
 * @param filename - Name of the file to download
 */
export async function downloadFile(filename: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/download/${encodeURIComponent(filename)}`);
  if (!response.ok) {
    throw new Error(`Download failed: ${response.statusText}`);
  }
  return response.blob();
}

// ===== Dify Integration API Functions =====

/**
 * Get stored Dify configuration
 * @returns Dify configuration with API key and base URL
 */
export async function getDifyConfig(): Promise<DifyConfig> {
  const response = await fetch(`${API_BASE_URL}/dify/config`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Failed to get Dify config: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Save or update Dify configuration
 * @param config - Dify configuration with API key and base URL
 * @returns Success status
 */
export async function saveDifyConfig(config: DifyConfig): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/dify/config`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Failed to save Dify config: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Test connection to Dify API
 * @param config - Dify configuration to test
 * @returns Connection test result
 */
export async function testDifyConnection(config: DifyConfig): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/dify/test-connection`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
    signal: AbortSignal.timeout(30000), // 30 seconds timeout
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Connection test failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * List all datasets in Dify Knowledge Base
 * @param page - Page number (1-indexed)
 * @param limit - Number of datasets per page
 * @returns List of Dify datasets
 */
export async function listDatasets(page: number = 1, limit: number = 20): Promise<DifyDataset[]> {
  const response = await fetch(`${API_BASE_URL}/dify/datasets?page=${page}&limit=${limit}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Failed to list datasets: ${response.statusText}`);
  }

  return response.json();
}

/**
 * List all parsed documents in the output folder
 * @returns List of parsed documents with database metadata
 */
export async function listParsedDocuments(): Promise<ParsedDocument[]> {
  const response = await fetch(`${API_BASE_URL}/dify/parsed-documents`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Failed to list parsed documents: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Upload a parsed document to Dify Knowledge Base
 * @param request - Upload request with dataset ID, document path, and name
 * @returns Upload response with document ID and batch ID
 */
export async function uploadToDify(request: UploadRequest): Promise<UploadResponse> {
  const response = await fetch(`${API_BASE_URL}/dify/upload`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
    signal: AbortSignal.timeout(300000), // 5 minutes timeout
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Failed to upload document: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Check indexing status of a document batch
 * @param dataset_id - Dataset ID
 * @param batch_id - Batch ID from upload response
 * @returns Indexing status with progress
 */
export async function getIndexingStatus(dataset_id: string, batch_id: string): Promise<IndexingStatus> {
  const response = await fetch(`${API_BASE_URL}/dify/status/${encodeURIComponent(dataset_id)}/${encodeURIComponent(batch_id)}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Failed to get indexing status: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get upload history
 * @param limit - Maximum number of records to return
 * @returns List of upload logs
 */
export async function getUploadHistory(limit: number = 50): Promise<DifyUploadLog[]> {
  const response = await fetch(`${API_BASE_URL}/dify/upload-history?limit=${limit}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Failed to get upload history: ${response.statusText}`);
  }

  return response.json();
}
