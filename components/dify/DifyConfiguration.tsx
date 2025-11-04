'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Settings, Database, CheckCircle } from 'lucide-react'
import type { DifyConfig, DifyDataset } from '@/lib/types'

interface DifyConfigurationProps {
  config: DifyConfig | null
  datasets: DifyDataset[]
  selectedDataset: string
  onConfigSave: (config: DifyConfig) => void
  onDatasetChange: (datasetId: string) => void
  onTest?: (config: DifyConfig) => Promise<boolean>
  loading?: boolean
}

export function DifyConfiguration({
  config,
  datasets,
  selectedDataset,
  onConfigSave,
  onDatasetChange,
  onTest,
  loading
}: DifyConfigurationProps) {
  const [apiKey, setApiKey] = useState(config?.api_key || '')
  const [baseUrl, setBaseUrl] = useState(config?.base_url || 'http://kca-ai.kro.kr:5001/v1')
  const [testing, setTesting] = useState(false)

  const handleSave = () => {
    onConfigSave({ api_key: apiKey, base_url: baseUrl })
  }

  const handleTest = async () => {
    if (!onTest) return
    setTesting(true)
    try {
      await onTest({ api_key: apiKey, base_url: baseUrl })
    } finally {
      setTesting(false)
    }
  }

  return (
    <Card className="gap-3 py-3">
      <CardContent className="px-4">
        <div className="flex flex-col gap-3">
          {/* First Row: Config Controls */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Title & Status */}
            <div className="flex items-center gap-2 shrink-0">
              <Settings className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold">Dify Config</span>
              {config?.api_key && (
                <CheckCircle className="h-3.5 w-3.5 text-green-600" />
              )}
            </div>

            {/* API Key */}
            <div className="flex items-center gap-2 shrink-0">
              <Label htmlFor="api-key" className="text-sm whitespace-nowrap">
                API Key
              </Label>
              <Input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="e.g., dataset-abc123"
                className="font-mono w-48"
              />
            </div>

            {/* Base URL */}
            <div className="flex items-center gap-2 shrink-0">
              <Label htmlFor="base-url" className="text-sm whitespace-nowrap">
                Base URL
              </Label>
              <Input
                id="base-url"
                type="text"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="e.g., http://kca-ai.kro.kr:5001/v1"
                className="font-mono w-64"
              />
            </div>

            {/* Buttons */}
            <div className="flex gap-2 ml-auto">
              <Button onClick={handleSave} size="sm">
                Save
              </Button>
              {onTest && (
                <Button
                  variant="outline"
                  onClick={handleTest}
                  disabled={testing}
                  size="sm"
                >
                  {testing ? 'Testing...' : 'Test'}
                </Button>
              )}
            </div>
          </div>

          {/* Second Row: Dataset Selector */}
          <div className="flex items-center gap-3">
            <Label htmlFor="dataset" className="text-sm whitespace-nowrap flex items-center gap-1.5 shrink-0">
              <Database className="h-3.5 w-3.5" />
              Dataset
            </Label>
            <div className="w-1/2">
              {loading ? (
                <div className="text-xs text-muted-foreground">Loading datasets...</div>
              ) : datasets.length === 0 ? (
                <div className="text-xs text-muted-foreground">
                  No datasets available. Check your API configuration.
                </div>
              ) : (
                <Select value={selectedDataset} onValueChange={onDatasetChange}>
                  <SelectTrigger id="dataset" className="w-full">
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
        </div>
      </CardContent>
    </Card>
  )
}
