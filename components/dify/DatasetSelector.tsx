'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Database } from 'lucide-react'
import type { DifyDataset } from '@/lib/types'

interface DatasetSelectorProps {
  datasets: DifyDataset[]
  selected: string
  onChange: (datasetId: string) => void
  loading?: boolean
}

export function DatasetSelector({ datasets, selected, onChange, loading }: DatasetSelectorProps) {
  return (
    <Card className="gap-2 py-3">
      <CardContent className="px-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 min-w-fit">
            <Database className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold whitespace-nowrap">Dataset</span>
          </div>

          <div className="flex-1">
            {loading ? (
              <div className="text-xs text-muted-foreground">Loading datasets...</div>
            ) : datasets.length === 0 ? (
              <div className="text-xs text-muted-foreground">
                No datasets available. Check your API configuration.
              </div>
            ) : (
              <Select value={selected} onValueChange={onChange}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Select a dataset" />
                </SelectTrigger>
                <SelectContent>
                  {datasets.map((dataset) => (
                    <SelectItem key={dataset.id} value={dataset.id}>
                      {dataset.name} ({dataset.document_count} docs, {(dataset.word_count / 1000).toFixed(0)}K words)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
