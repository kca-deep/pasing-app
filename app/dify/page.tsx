'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { DifyConfiguration } from '@/components/dify/DifyConfiguration'
import { ParsedDocumentSelector } from '@/components/dify/ParsedDocumentSelector'
import { DifyUploadProgress } from '@/components/dify/DifyUploadProgress'
import {
  getDifyConfig,
  saveDifyConfig,
  testDifyConnection,
  listDatasets,
  listParsedDocuments,
  uploadToDify,
  getIndexingStatus
} from '@/lib/api'
import type { DifyConfig, DifyDataset, ParsedDocument, DocumentUploadStatus } from '@/lib/types'
import { Database, Sparkles, Upload } from 'lucide-react'
import { toast } from 'sonner'

export default function DifyPage() {
  // State
  const [config, setConfig] = useState<DifyConfig | null>(null)
  const [datasets, setDatasets] = useState<DifyDataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [parsedDocs, setParsedDocs] = useState<ParsedDocument[]>([])
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])
  const [uploading, setUploading] = useState(false)
  const [documentsUploadStatus, setDocumentsUploadStatus] = useState<DocumentUploadStatus[]>([])

  // Loading states
  const [loadingConfig, setLoadingConfig] = useState(true)
  const [loadingDatasets, setLoadingDatasets] = useState(false)
  const [loadingDocs, setLoadingDocs] = useState(false)

  // Load initial data
  useEffect(() => {
    loadConfig()
    loadParsedDocuments()
  }, [])

  // Load datasets when config changes (only if API key is valid)
  useEffect(() => {
    if (config && config.api_key && config.api_key.trim()) {
      loadDatasets()
    }
  }, [config])

  const loadConfig = async () => {
    try {
      setLoadingConfig(true)
      const savedConfig = await getDifyConfig()
      setConfig(savedConfig)
    } catch (error: any) {
      // Config not found is ok, user needs to set it up
      if (!error.message.includes('404') && !error.message.includes('not found')) {
        console.error('Failed to load config:', error)
        toast.error('Failed to load configuration')
      }
    } finally {
      setLoadingConfig(false)
    }
  }

  const loadDatasets = async () => {
    // Check if config has valid API key
    if (!config || !config.api_key || !config.api_key.trim()) {
      console.log('Skipping dataset load: No valid API key')
      return
    }

    try {
      setLoadingDatasets(true)
      const datasetList = await listDatasets(1, 20)
      setDatasets(datasetList)
    } catch (error: any) {
      console.error('Failed to load datasets:', error)
      toast.error('Failed to load datasets: ' + error.message)
    } finally {
      setLoadingDatasets(false)
    }
  }

  const loadParsedDocuments = async () => {
    try {
      setLoadingDocs(true)
      const docs = await listParsedDocuments()
      setParsedDocs(docs)
    } catch (error: any) {
      console.error('Failed to load parsed documents:', error)
      toast.error('Failed to load parsed documents: ' + error.message)
    } finally {
      setLoadingDocs(false)
    }
  }

  const handleSaveConfig = async (newConfig: DifyConfig) => {
    try {
      await saveDifyConfig(newConfig)
      setConfig(newConfig)
      toast.success('Configuration saved successfully!')

      // Reload datasets with new config (only if API key is valid)
      if (newConfig.api_key && newConfig.api_key.trim()) {
        await loadDatasets()
      }
    } catch (error: any) {
      console.error('Failed to save config:', error)
      toast.error('Failed to save configuration: ' + error.message)
    }
  }

  const handleTestConnection = async (testConfig: DifyConfig): Promise<boolean> => {
    try {
      const result = await testDifyConnection(testConfig)
      if (result.success) {
        toast.success('Connection successful!')
      } else {
        toast.error('Connection failed: ' + result.message)
      }
      return result.success
    } catch (error: any) {
      console.error('Connection test failed:', error)
      toast.error('Connection test failed: ' + error.message)
      return false
    }
  }

  const pollIndexingStatus = async (datasetId: string, batchId: string, docIndex: number) => {
    let attempts = 0
    const maxAttempts = 60 // 60 attempts * 3 seconds = 3 minutes max

    const poll = async () => {
      try {
        const status = await getIndexingStatus(datasetId, batchId)

        // Update progress based on status
        if (status.total_segments > 0) {
          const progress = Math.round((status.completed_segments / status.total_segments) * 100)
          setDocumentsUploadStatus(prev =>
            prev.map((doc, idx) =>
              idx === docIndex ? { ...doc, progress } : doc
            )
          )
        }

        // Check if completed or error
        if (status.indexing_status === 'completed') {
          setDocumentsUploadStatus(prev =>
            prev.map((doc, idx) =>
              idx === docIndex ? { ...doc, status: 'completed', progress: 100 } : doc
            )
          )
          return true
        } else if (status.indexing_status === 'error') {
          setDocumentsUploadStatus(prev =>
            prev.map((doc, idx) =>
              idx === docIndex ? { ...doc, status: 'error', error: 'Indexing failed' } : doc
            )
          )
          return false
        }

        // Continue polling
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(() => poll(), 3000) // Poll every 3 seconds
        } else {
          // Timeout
          setDocumentsUploadStatus(prev =>
            prev.map((doc, idx) =>
              idx === docIndex ? { ...doc, status: 'error', error: 'Indexing timeout' } : doc
            )
          )
        }
      } catch (error: any) {
        console.error('Failed to check indexing status:', error)
        setDocumentsUploadStatus(prev =>
          prev.map((doc, idx) =>
            idx === docIndex ? { ...doc, status: 'error', error: 'Status check failed' } : doc
          )
        )
      }
    }

    poll()
  }

  const handleUpload = async () => {
    if (!selectedDataset || selectedDocs.length === 0 || !config) return

    setUploading(true)

    // Initialize upload status for all selected documents
    const selectedDocuments = parsedDocs.filter(doc => selectedDocs.includes(doc.path))
    const initialStatuses: DocumentUploadStatus[] = selectedDocuments.map(doc => ({
      path: doc.path,
      name: doc.name,
      status: 'waiting',
      progress: 0
    }))
    setDocumentsUploadStatus(initialStatuses)

    // Upload documents sequentially
    for (let i = 0; i < selectedDocuments.length; i++) {
      const doc = selectedDocuments[i]

      try {
        // Start uploading
        setDocumentsUploadStatus(prev =>
          prev.map((status, idx) =>
            idx === i ? { ...status, status: 'uploading', progress: 0 } : status
          )
        )

        // Upload document
        const response = await uploadToDify({
          dataset_id: selectedDataset,
          document_path: doc.path,
          document_name: doc.name,
          indexing_technique: 'high_quality'
        })

        // Update status with document ID
        setDocumentsUploadStatus(prev =>
          prev.map((status, idx) =>
            idx === i ? {
              ...status,
              document_id: response.document_id,
              progress: 50
            } : status
          )
        )

        // Start polling indexing status
        if (response.batch_id) {
          pollIndexingStatus(selectedDataset, response.batch_id, i)
        } else {
          // No batch ID, mark as completed immediately
          setDocumentsUploadStatus(prev =>
            prev.map((status, idx) =>
              idx === i ? { ...status, status: 'completed', progress: 100 } : status
            )
          )
        }

        toast.success(`Uploaded: ${doc.name}`)
      } catch (error: any) {
        console.error(`Failed to upload ${doc.name}:`, error)
        setDocumentsUploadStatus(prev =>
          prev.map((status, idx) =>
            idx === i ? {
              ...status,
              status: 'error',
              progress: 0,
              error: error.message || 'Upload failed'
            } : status
          )
        )
        toast.error(`Failed to upload ${doc.name}: ${error.message}`)
      }

      // Small delay between documents
      await new Promise(resolve => setTimeout(resolve, 500))
    }

    setUploading(false)
    toast.success('Batch upload completed!')
  }

  const canUpload = !uploading && selectedDataset && selectedDocs.length > 0 && config

  if (loadingConfig) {
    return (
      <div className="container mx-auto py-6 px-4 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading configuration...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 px-4">
      <div className="max-w-7xl mx-auto space-y-3">
        {/* Hero Section */}
        <div className="animate-fade-in-up">
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
            Dify Knowledge Base Upload
            <Database className="h-7 w-7 text-primary animate-pulse" />
          </h1>
          <p className="text-muted-foreground text-sm flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-accent" />
            Upload parsed documents to your Dify knowledge base for AI-powered retrieval
          </p>
        </div>

        {/* Configuration */}
        <div className="animate-fade-in-up">
          <DifyConfiguration
            config={config}
            datasets={datasets}
            selectedDataset={selectedDataset}
            onConfigSave={handleSaveConfig}
            onDatasetChange={setSelectedDataset}
            onTest={handleTestConnection}
            loading={loadingDatasets}
          />
        </div>

        {/* Document Selection - Full Width */}
        <div className="animate-fade-in-up">
          <ParsedDocumentSelector
            documents={parsedDocs}
            selectedDocs={selectedDocs}
            onChange={setSelectedDocs}
            loading={loadingDocs}
            onRefresh={loadParsedDocuments}
          />
        </div>

        {/* Upload Actions */}
        <div className="space-y-2 animate-fade-in-up">
          <Button
            className="w-full transition-all hover:scale-[1.02] hover:shadow-lg"
            size="lg"
            onClick={handleUpload}
            disabled={!canUpload}
          >
            <Upload className="mr-2 h-5 w-5" />
            {uploading ? 'Uploading...' : `Upload ${selectedDocs.length} document(s) to Dify`}
          </Button>

          {uploading && (
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setUploading(false)}
            >
              Cancel Upload
            </Button>
          )}
        </div>

        {documentsUploadStatus.length > 0 && (
          <div className="animate-fade-in">
            <DifyUploadProgress documents={documentsUploadStatus} />
          </div>
        )}
      </div>
    </div>
  )
}
