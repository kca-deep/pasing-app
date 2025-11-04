'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import type { IndexingStatus } from '@/lib/types'

interface UploadProgressProps {
  status: IndexingStatus | null
}

export function UploadProgress({ status }: UploadProgressProps) {
  if (!status) return null

  const progress = status.total_segments > 0
    ? (status.completed_segments / status.total_segments) * 100
    : 0

  const getStatusColor = () => {
    switch (status.indexing_status) {
      case 'completed': return 'text-green-600'
      case 'error': return 'text-red-600'
      case 'indexing': return 'text-blue-600'
      default: return 'text-yellow-600'
    }
  }

  const getStatusText = () => {
    switch (status.indexing_status) {
      case 'waiting': return 'Waiting to start...'
      case 'indexing': return 'Vectorizing document...'
      case 'completed': return 'Upload completed!'
      case 'error': return 'Upload failed'
    }
  }

  return (
    <Card className="border-2 gap-2 py-3">
      <CardHeader className="pb-0 px-4">
        <CardTitle className="flex items-center justify-between text-base">
          <span>Upload Progress</span>
          <span className={`text-xs font-normal ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </CardTitle>
        <CardDescription className="text-xs">
          Vectorizing document for AI retrieval
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 px-4">
        <div className="space-y-2">
          <Progress value={progress} className="h-3" />
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              {status.completed_segments} / {status.total_segments} segments
            </span>
            <span className={`font-semibold ${getStatusColor()}`}>
              {progress.toFixed(0)}%
            </span>
          </div>
        </div>
        {status.error && (
          <div className="rounded-md bg-red-50 dark:bg-red-950/30 p-2 text-sm text-red-600 dark:text-red-400">
            <p className="font-medium">Error:</p>
            <p>{status.error}</p>
          </div>
        )}
        {status.completed_at && (
          <div className="rounded-md bg-green-50 dark:bg-green-950/30 p-2 text-sm text-green-600 dark:text-green-400">
            Completed at: {new Date(status.completed_at).toLocaleString('ko-KR')}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
