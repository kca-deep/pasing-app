'use client';

import { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  RadioGroup,
  RadioGroupItem,
} from '@/components/ui/radio-group';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import type { ParseOptions } from '@/lib/types';
import { Sparkles, Zap, FileText, ScanText, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ParsingOptionsProps {
  options: ParseOptions;
  onOptionsChange: (options: ParseOptions) => void;
}

type ParsingStrategy = 'docling' | 'camelot' | 'remote_ocr' | 'mineru';

// Strategy definitions with icons and metadata (ordered by recommendation)
const strategies = [
  {
    value: 'docling',
    label: 'Docling Only',
    subtitle: 'Basic',
    icon: FileText,
    description: '📄 Basic Document Parsing',
    details: 'Fast parsing for simple documents without advanced table extraction',
    color: 'text-slate-600',
    bgColor: 'bg-slate-50',
    borderColor: 'border-slate-200'
  },
  {
    value: 'camelot',
    label: 'Docling + Camelot',
    subtitle: 'Hybrid',
    icon: Zap,
    description: '⚡ High-Accuracy Table Extraction',
    details: 'Best for PDFs with complex tables. Combines Camelot (tables) + Docling (text)',
    color: 'text-orange-500',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200'
  },
  {
    value: 'remote_ocr',
    label: 'Remote OCR',
    subtitle: 'Korean Optimized',
    icon: ScanText,
    badge: 'New',
    badgeVariant: 'default' as const,
    description: '🇰🇷 Korean Document OCR',
    details: 'Remote OCR server with PaddleOCR (90%+ Korean accuracy). Perfect for scanned documents',
    color: 'text-blue-500',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200'
  },
  {
    value: 'mineru',
    label: 'MinerU',
    subtitle: 'Universal',
    icon: Sparkles,
    description: '✨ Universal PDF Parser',
    details: 'Advanced: merged cells, hierarchical tables, auto text ordering, 84 languages',
    color: 'text-purple-500',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200'
  },
] as const;

export function ParsingOptions({ options, onOptionsChange }: ParsingOptionsProps) {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const updateOption = <K extends keyof ParseOptions>(key: K, value: ParseOptions[K]) => {
    onOptionsChange({ ...options, [key]: value });
  };

  // Determine current strategy based on options
  const getCurrentStrategy = (): ParsingStrategy => {
    if (options.use_remote_ocr) return 'remote_ocr';
    if (options.use_mineru) return 'mineru';
    if (options.use_camelot !== false) return 'camelot'; // Default
    return 'docling';
  };

  const currentStrategy = getCurrentStrategy();
  const currentStrategyData = strategies.find(s => s.value === currentStrategy);

  const handleStrategyChange = (strategy: ParsingStrategy) => {
    const newOptions = { ...options };

    // Reset strategy flags
    newOptions.use_remote_ocr = false;
    newOptions.use_mineru = false;
    newOptions.use_camelot = false;

    // Set selected strategy
    if (strategy === 'remote_ocr') {
      newOptions.use_remote_ocr = true;
      newOptions.remote_ocr_engine = newOptions.remote_ocr_engine || 'paddleocr';
      newOptions.remote_ocr_languages = newOptions.remote_ocr_languages || ['kor', 'eng'];
    } else if (strategy === 'mineru') {
      newOptions.use_mineru = true;
      newOptions.mineru_lang = newOptions.mineru_lang || 'auto';
      newOptions.mineru_use_ocr = newOptions.mineru_use_ocr ?? true;
    } else if (strategy === 'camelot') {
      newOptions.use_camelot = true;
      newOptions.camelot_mode = newOptions.camelot_mode || 'hybrid';
    }
    // docling: all false (default Docling behavior)

    onOptionsChange(newOptions);
  };

  return (
    <div className="space-y-6">
      {/* Parsing Strategy Card */}
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Parsing Strategy
          </CardTitle>
          <CardDescription>
            Choose the parsing engine for your document
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Select value={currentStrategy} onValueChange={(value) => handleStrategyChange(value as ParsingStrategy)}>
            <SelectTrigger className="w-full h-auto py-3">
              <SelectValue>
                {currentStrategyData && (
                  <div className="flex items-center gap-3">
                    <currentStrategyData.icon className={cn("h-5 w-5", currentStrategyData.color)} />
                    <div className="flex flex-col items-start">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{currentStrategyData.label}</span>
                        {currentStrategyData.badge && (
                          <Badge variant={currentStrategyData.badgeVariant} className="text-xs h-5">
                            {currentStrategyData.badge}
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground">{currentStrategyData.subtitle}</span>
                    </div>
                  </div>
                )}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {strategies.map((strategy) => {
                const Icon = strategy.icon;
                return (
                  <SelectItem
                    key={strategy.value}
                    value={strategy.value}
                    className="py-3"
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={cn("h-5 w-5", strategy.color)} />
                      <div className="flex flex-col items-start">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{strategy.label}</span>
                          {strategy.badge && (
                            <Badge variant={strategy.badgeVariant} className="text-xs h-5">
                              {strategy.badge}
                            </Badge>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">{strategy.subtitle}</span>
                      </div>
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>

          {/* Strategy Description */}
          {currentStrategyData && (
            <div className={cn(
              "text-xs p-4 rounded-lg border",
              currentStrategyData.bgColor,
              currentStrategyData.borderColor
            )}>
              <p className={cn("font-semibold mb-1.5", currentStrategyData.color)}>
                {currentStrategyData.description}
              </p>
              <p className="text-muted-foreground">{currentStrategyData.details}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Strategy-Specific Options */}
      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <Card>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-accent/5 transition-colors">
              <CardTitle className="text-base flex items-center justify-between">
                <span>Advanced Options</span>
                <ChevronDown className={cn(
                  "h-4 w-4 transition-transform duration-200",
                  advancedOpen && "transform rotate-180"
                )} />
              </CardTitle>
            </CardHeader>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <CardContent className="space-y-6 pt-0">
          {/* Remote OCR-specific options */}
          {currentStrategy === 'remote_ocr' && (
            <>
              <div className="space-y-3">
                <Label>OCR Engine</Label>
                <RadioGroup
                  value={options.remote_ocr_engine || 'paddleocr'}
                  onValueChange={(value) => updateOption('remote_ocr_engine', value as 'tesseract' | 'paddleocr')}
                  className="space-y-2"
                >
                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="paddleocr" id="ocr-paddle" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="ocr-paddle" className="flex items-center gap-2 cursor-pointer">
                        <span className="font-semibold">🎯 PaddleOCR</span>
                        <Badge variant="default" className="text-xs">⭐ Recommended</Badge>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        High-accuracy OCR optimized for Korean (~1.6s)
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="tesseract" id="ocr-tesseract" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="ocr-tesseract" className="flex items-center gap-2 cursor-pointer">
                        <span className="font-semibold">⚡ Tesseract</span>
                        <Badge variant="secondary" className="text-xs">Fast</Badge>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Fast OCR for simple documents (~0.2s)
                      </p>
                    </div>
                  </div>
                </RadioGroup>
              </div>

              <div className="space-y-2">
                <Label>🌐 Languages</Label>
                <div className="flex gap-2 flex-wrap">
                  <Badge variant="default" className="bg-blue-500">🇰🇷 Korean</Badge>
                  <Badge variant="secondary">🇺🇸 English</Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Automatically detects Korean and English text
                </p>
              </div>

              <div className="bg-blue-50 p-3 rounded-md border border-blue-200">
                <p className="text-xs font-semibold mb-1 text-blue-600">📡 Remote Server</p>
                <p className="text-xs text-muted-foreground">
                  OCR processing is done on remote server (kca-ai.kro.kr:8005)
                </p>
              </div>
            </>
          )}

          {/* MinerU-specific options */}
          {currentStrategy === 'mineru' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="mineru-lang">🌐 Language</Label>
                <Select
                  value={options.mineru_lang || 'auto'}
                  onValueChange={(value) => updateOption('mineru_lang', value as 'auto' | 'ko' | 'zh' | 'en' | 'ja')}
                >
                  <SelectTrigger id="mineru-lang">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">🔄 Auto-detect</SelectItem>
                    <SelectItem value="ko">🇰🇷 Korean (한국어)</SelectItem>
                    <SelectItem value="zh">🇨🇳 Chinese (中文)</SelectItem>
                    <SelectItem value="en">🇺🇸 English</SelectItem>
                    <SelectItem value="ja">🇯🇵 Japanese (日本語)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  MinerU supports 84 languages with automatic detection
                </p>
              </div>

              <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="mineru-ocr" className="cursor-pointer font-semibold">🔍 Enable OCR</Label>
                  <p className="text-sm text-muted-foreground">
                    Extract text from scanned documents
                  </p>
                </div>
                <Switch
                  id="mineru-ocr"
                  checked={options.mineru_use_ocr ?? true}
                  onCheckedChange={(checked) => updateOption('mineru_use_ocr', checked)}
                />
              </div>

              <div className="bg-purple-50 p-3 rounded-md border border-purple-200">
                <p className="text-xs font-semibold mb-1 text-purple-600">✨ Universal Parser</p>
                <p className="text-xs text-muted-foreground">
                  Handles merged cells, hierarchical tables, and automatic text ordering
                </p>
              </div>
            </>
          )}

          {/* Camelot-specific options */}
          {currentStrategy === 'camelot' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="camelot-mode">📊 Table Extraction Mode</Label>
                <Select
                  value={options.camelot_mode || 'hybrid'}
                  onValueChange={(value) => updateOption('camelot_mode', value as 'lattice' | 'stream' | 'hybrid')}
                >
                  <SelectTrigger id="camelot-mode">
                    <SelectValue placeholder="Select mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hybrid">⭐ Hybrid (Lattice + Stream)</SelectItem>
                    <SelectItem value="lattice">🔲 Lattice (Bordered tables)</SelectItem>
                    <SelectItem value="stream">📋 Stream (Borderless tables)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="table-mode">🎯 Table Parsing Accuracy</Label>
                <Select
                  value={options.table_mode || 'accurate'}
                  onValueChange={(value) => updateOption('table_mode', value)}
                >
                  <SelectTrigger id="table-mode">
                    <SelectValue placeholder="Select accuracy" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="accurate">⭐ Accurate (Slower, precise)</SelectItem>
                    <SelectItem value="fast">⚡ Fast (Quick extraction)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="ocr-switch" className="cursor-pointer font-semibold">🔍 Enable OCR</Label>
                  <p className="text-sm text-muted-foreground">
                    Extract text from images and scanned documents
                  </p>
                </div>
                <Switch
                  id="ocr-switch"
                  checked={options.do_ocr ?? false}
                  onCheckedChange={(checked) => updateOption('do_ocr', checked)}
                />
              </div>

              {/* OCR Engine Info (only shown when OCR is enabled) */}
              {options.do_ocr && (
                <div className="rounded-lg bg-orange-50 border border-orange-200 p-3">
                  <p className="text-xs font-semibold text-orange-600 mb-1">
                    🔍 OCR Engine: EasyOCR
                  </p>
                  <p className="text-xs text-muted-foreground">
                    High accuracy for Korean & English (built-in, no installation needed)
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    💡 <strong>Want other OCR engines?</strong> Use "Remote OCR" strategy for Tesseract/PaddleOCR.
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center space-x-2 rounded-lg border p-3">
                  <Switch
                    id="tables-html"
                    checked={options.tables_as_html ?? false}
                    onCheckedChange={(checked) => updateOption('tables_as_html', checked)}
                  />
                  <Label htmlFor="tables-html" className="cursor-pointer text-sm">📝 Tables as HTML</Label>
                </div>

                <div className="flex items-center space-x-2 rounded-lg border p-3">
                  <Switch
                    id="cell-matching"
                    checked={options.do_cell_matching ?? false}
                    onCheckedChange={(checked) => updateOption('do_cell_matching', checked)}
                  />
                  <Label htmlFor="cell-matching" className="cursor-pointer text-sm">🔗 Cell Matching</Label>
                </div>

                <div className="flex items-center space-x-2 rounded-lg border p-3">
                  <Switch
                    id="picture-desc"
                    checked={options.do_picture_description ?? false}
                    onCheckedChange={(checked) => updateOption('do_picture_description', checked)}
                  />
                  <Label htmlFor="picture-desc" className="cursor-pointer text-sm">🖼️ Picture VLM</Label>
                </div>

                <div className="flex items-center space-x-2 rounded-lg border p-3">
                  <Switch
                    id="auto-image"
                    checked={options.auto_image_analysis ?? false}
                    onCheckedChange={(checked) => updateOption('auto_image_analysis', checked)}
                  />
                  <Label htmlFor="auto-image" className="cursor-pointer text-sm">🤖 Auto Image AI</Label>
                </div>
              </div>
            </>
          )}

          {/* Docling-specific options */}
          {currentStrategy === 'docling' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="docling-table-mode">🎯 Table Parsing Accuracy</Label>
                <Select
                  value={options.table_mode || 'accurate'}
                  onValueChange={(value) => updateOption('table_mode', value)}
                >
                  <SelectTrigger id="docling-table-mode">
                    <SelectValue placeholder="Select accuracy" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="accurate">⭐ Accurate (Slower, precise)</SelectItem>
                    <SelectItem value="fast">⚡ Fast (Quick extraction)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="docling-ocr" className="cursor-pointer font-semibold">🔍 Enable OCR</Label>
                  <p className="text-sm text-muted-foreground">
                    Extract text from images and scanned documents
                  </p>
                </div>
                <Switch
                  id="docling-ocr"
                  checked={options.do_ocr ?? false}
                  onCheckedChange={(checked) => updateOption('do_ocr', checked)}
                />
              </div>

              {/* OCR Engine Info (only shown when OCR is enabled) */}
              {options.do_ocr && (
                <div className="rounded-lg bg-slate-100 border border-slate-300 p-3">
                  <p className="text-xs font-semibold text-slate-700 mb-1">
                    🔍 OCR Engine: EasyOCR
                  </p>
                  <p className="text-xs text-muted-foreground">
                    High accuracy for Korean & English (built-in, no installation needed)
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    💡 <strong>Want other OCR engines?</strong> Use "Remote OCR" strategy for Tesseract/PaddleOCR.
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center space-x-2 rounded-lg border p-3">
                  <Switch
                    id="docling-tables-html"
                    checked={options.tables_as_html ?? false}
                    onCheckedChange={(checked) => updateOption('tables_as_html', checked)}
                  />
                  <Label htmlFor="docling-tables-html" className="cursor-pointer text-sm">📝 Tables as HTML</Label>
                </div>

                <div className="flex items-center space-x-2 rounded-lg border p-3">
                  <Switch
                    id="docling-cell-matching"
                    checked={options.do_cell_matching ?? false}
                    onCheckedChange={(checked) => updateOption('do_cell_matching', checked)}
                  />
                  <Label htmlFor="docling-cell-matching" className="cursor-pointer text-sm">🔗 Cell Matching</Label>
                </div>

                <div className="flex items-center space-x-2 rounded-lg border p-3">
                  <Switch
                    id="docling-picture-desc"
                    checked={options.do_picture_description ?? false}
                    onCheckedChange={(checked) => updateOption('do_picture_description', checked)}
                  />
                  <Label htmlFor="docling-picture-desc" className="cursor-pointer text-sm">🖼️ Picture VLM</Label>
                </div>

                <div className="flex items-center space-x-2 rounded-lg border p-3">
                  <Switch
                    id="docling-auto-image"
                    checked={options.auto_image_analysis ?? false}
                    onCheckedChange={(checked) => updateOption('auto_image_analysis', checked)}
                  />
                  <Label htmlFor="docling-auto-image" className="cursor-pointer text-sm">🤖 Auto Image AI</Label>
                </div>
              </div>
            </>
          )}

          {/* Common Options */}
          <div className="pt-6 border-t space-y-4">
            <div className="space-y-2">
              <Label htmlFor="output-format">📤 Output Format</Label>
              <Select
                value={options.output_format || 'markdown'}
                onValueChange={(value) => updateOption('output_format', value as 'markdown' | 'html' | 'json')}
              >
                <SelectTrigger id="output-format">
                  <SelectValue placeholder="Select format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="markdown">📝 Markdown (.md)</SelectItem>
                  <SelectItem value="html">🌐 HTML (.html)</SelectItem>
                  <SelectItem value="json">📋 JSON (.json)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/5 transition-colors">
              <div className="space-y-0.5 flex-1">
                <Label htmlFor="extract-tables" className="cursor-pointer font-semibold">📊 Extract Tables</Label>
                <p className="text-sm text-muted-foreground">
                  Save tables separately as JSON and CSV
                </p>
              </div>
              <Switch
                id="extract-tables"
                checked={options.extract_tables ?? true}
                onCheckedChange={(checked) => updateOption('extract_tables', checked)}
              />
            </div>

            <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/5 transition-colors">
              <div className="space-y-0.5 flex-1">
                <Label htmlFor="save-output" className="cursor-pointer font-semibold">💾 Save to Output Folder</Label>
                <p className="text-sm text-muted-foreground">
                  Save parsed content to structured output folder
                </p>
              </div>
              <Switch
                id="save-output"
                checked={options.save_to_output_folder ?? true}
                onCheckedChange={(checked) => updateOption('save_to_output_folder', checked)}
              />
            </div>
          </div>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>
    </div>
  );
}
