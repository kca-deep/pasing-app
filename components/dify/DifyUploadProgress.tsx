'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { CheckCircle2, Clock, Loader2, XCircle, Upload } from 'lucide-react'
import type { DocumentUploadStatus } from '@/lib/types'

interface DifyUploadProgressProps {
  documents: DocumentUploadStatus[]
}

export function DifyUploadProgress({ documents }: DifyUploadProgressProps) {
  if (documents.length === 0) return null

  const completed = documents.filter(d => d.status === 'completed').length
  const errored = documents.filter(d => d.status === 'error').length
  const total = documents.length
  const overallProgress = (completed / total) * 100

  const getStatusIcon = (status: DocumentUploadStatus['status']) => {
    switch (status) {
      case 'waiting':
        return <Clock className="h-4 w-4 text-muted-foreground" />
      case 'uploading':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />
    }
  }

  const getStatusColor = (status: DocumentUploadStatus['status']) => {
    switch (status) {
      case 'waiting':
        return 'text-muted-foreground'
      case 'uploading':
        return 'text-blue-600'
      case 'completed':
        return 'text-green-600'
      case 'error':
        return 'text-red-600'
    }
  }

  const getStatusText = (status: DocumentUploadStatus['status']) => {
    switch (status) {
      case 'waiting':
        return 'Waiting...'
      case 'uploading':
        return 'Uploading...'
      case 'completed':
        return 'Completed'
      case 'error':
        return 'Failed'
    }
  }

  return (
    <Card className="gap-3 py-4 animate-fade-in">
      <CardHeader className="pb-0 px-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <Upload className="h-4 w-4" />
          Upload Progress
          <span className="text-xs font-normal text-muted-foreground ml-auto">
            {completed} of {total} completed
            {errored > 0 && ` • ${errored} failed`}
          </span>
        </CardTitle>
        <CardDescription className="text-xs">
          Uploading documents to Dify knowledge base
        </CardDescription>
      </CardHeader>
      <CardContent className="px-4">
        <div className="space-y-4">
          {/* Overall Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Overall Progress</span>
              <span className="font-medium">{overallProgress.toFixed(0)}%</span>
            </div>
            <Progress value={overallProgress} className="h-2" />
          </div>

          {/* Individual Documents */}
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.path}
                className="space-y-2 p-3 rounded-lg border bg-accent/30"
              >
                <div className="flex items-center gap-2">
                  {getStatusIcon(doc.status)}
                  <span className="font-medium text-sm flex-1 truncate">
                    {doc.name}
                  </span>
                  <span className={`text-xs ${getStatusColor(doc.status)}`}>
                    {getStatusText(doc.status)}
                  </span>
                </div>

                {doc.status === 'uploading' && (
                  <div className="space-y-1">
                    <Progress value={doc.progress} className="h-1.5" />
                    <p className="text-xs text-muted-foreground text-center animate-pulse">
                      Indexing document segments... {doc.progress.toFixed(0)}%
                    </p>
                  </div>
                )}

                {doc.status === 'error' && doc.error && (
                  <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 p-2 rounded">
                    {doc.error}
                  </div>
                )}

                {doc.status === 'completed' && (
                  <div className="text-xs text-green-600 dark:text-green-400">
                    Successfully uploaded and indexed
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
