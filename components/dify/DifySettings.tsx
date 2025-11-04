'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Settings, CheckCircle } from 'lucide-react'
import type { DifyConfig } from '@/lib/types'

interface DifySettingsProps {
  config: DifyConfig | null
  onSave: (config: DifyConfig) => void
  onTest?: (config: DifyConfig) => Promise<boolean>
}

export function DifySettings({ config, onSave, onTest }: DifySettingsProps) {
  const [apiKey, setApiKey] = useState(config?.api_key || '')
  const [baseUrl, setBaseUrl] = useState(config?.base_url || 'http://kca-ai.kro.kr:5001/v1')
  const [testing, setTesting] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

  const handleSave = () => {
    onSave({ api_key: apiKey, base_url: baseUrl })
  }

  const handleTest = async () => {
    if (!onTest) return
    setTesting(true)
    try {
      const result = await onTest({ api_key: apiKey, base_url: baseUrl })
      alert(result ? 'Connection successful!' : 'Connection failed!')
    } finally {
      setTesting(false)
    }
  }

  return (
    <Card className="gap-2 py-3">
      <CardContent className="px-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 min-w-fit">
            <Settings className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold whitespace-nowrap">Dify Config</span>
            {config?.api_key && (
              <CheckCircle className="h-3.5 w-3.5 text-green-600" />
            )}
          </div>

          <div className="flex-1 flex items-center gap-3">
            <div className="flex-1 min-w-[200px]">
              <Input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="dataset-xxxxxxxxxxxx"
                className="h-9 font-mono text-xs"
              />
            </div>

            <div className="flex-1 min-w-[200px]">
              <Input
                id="base-url"
                type="text"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="http://kca-ai.kro.kr:5001/v1"
                className="h-9 font-mono text-xs"
              />
            </div>

            <div className="flex gap-2 min-w-fit">
              <Button onClick={handleSave} size="sm" className="h-9 px-3 text-xs">
                Save
              </Button>
              {onTest && (
                <Button
                  variant="outline"
                  onClick={handleTest}
                  disabled={testing}
                  size="sm"
                  className="h-9 px-3 text-xs"
                >
                  {testing ? 'Testing...' : 'Test'}
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
