// API Client for FastAPI Backend

import type { DocumentInfo, ParseRequest, ParseResponse } from './types';

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
 * Parse a document using the FastAPI backend
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
