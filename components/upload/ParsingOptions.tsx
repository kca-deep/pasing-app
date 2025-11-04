'use client';

import { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
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
import { Sparkles, Zap, FileText, ScanText, Check, ChevronsUpDown, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ParsingOptionsProps {
  options: ParseOptions;
  onOptionsChange: (options: ParseOptions) => void;
}

type ParsingStrategy = 'remote_ocr' | 'dolphin' | 'mineru' | 'camelot' | 'docling';

// Strategy definitions with icons and metadata
const strategies = [
  {
    value: 'remote_ocr',
    label: 'Remote OCR',
    subtitle: 'Korean Optimized',
    icon: ScanText,
    badge: 'New',
    badgeVariant: 'default' as const,
    description: '🇰🇷 Korean Document OCR (High Accuracy)',
    details: 'Remote OCR server with PaddleOCR-VL (90%+ Korean accuracy) or Tesseract (fast). Perfect for scanned documents and images.',
    color: 'text-primary'
  },
  {
    value: 'camelot',
    label: 'Camelot + Docling',
    subtitle: 'Hybrid',
    icon: Zap,
    description: 'High-Accuracy Table Extraction',
    details: 'Best for PDFs with complex tables. Combines Camelot (tables) + Docling (text)',
    color: 'text-accent'
  },
  {
    value: 'docling',
    label: 'Docling Only',
    subtitle: 'Basic',
    icon: FileText,
    description: 'Basic Document Parsing',
    details: 'Fast parsing for simple documents without advanced table extraction',
    color: 'text-muted-foreground'
  },
  {
    value: 'dolphin',
    label: 'Dolphin Remote GPU',
    subtitle: 'AI-Powered',
    icon: Zap,
    badge: 'GPU',
    badgeVariant: 'outline' as const,
    description: '🚀 AI-Powered Remote GPU Parser',
    details: 'ByteDance Dolphin 1.5 on Remote GPU: High accuracy multimodal AI (0.3B model, OmniDocBench 83.21). Best for English/Chinese technical documents.',
    color: 'text-accent'
  },
  {
    value: 'mineru',
    label: 'MinerU',
    subtitle: 'Universal',
    icon: Sparkles,
    description: 'Universal PDF Parser',
    details: 'Advanced features: merged cells, hierarchical tables, automatic text ordering, 84 languages support',
    color: 'text-primary'
  },
] as const;

export function ParsingOptions({ options, onOptionsChange }: ParsingOptionsProps) {
  const [open, setOpen] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const updateOption = <K extends keyof ParseOptions>(key: K, value: ParseOptions[K]) => {
    onOptionsChange({ ...options, [key]: value });
  };

  // Determine current strategy based on options
  const getCurrentStrategy = (): ParsingStrategy => {
    if (options.use_remote_ocr) return 'remote_ocr';
    if (options.use_dolphin) return 'dolphin';
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
    newOptions.use_dolphin = false;
    newOptions.use_mineru = false;
    newOptions.use_camelot = false;

    // Set selected strategy
    if (strategy === 'remote_ocr') {
      newOptions.use_remote_ocr = true;
      newOptions.remote_ocr_engine = newOptions.remote_ocr_engine || 'paddleocr';
      newOptions.remote_ocr_languages = newOptions.remote_ocr_languages || ['kor', 'eng'];
    } else if (strategy === 'dolphin') {
      newOptions.use_dolphin = true;
      newOptions.dolphin_parsing_level = newOptions.dolphin_parsing_level || 'page';
      newOptions.dolphin_max_batch_size = newOptions.dolphin_max_batch_size || 8;
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
            <Badge variant="default" className="ml-auto">Remote OCR New!</Badge>
          </CardTitle>
          <CardDescription>
            Choose the parsing engine for your document (Remote OCR for Korean documents)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                aria-expanded={open}
                className="w-full justify-between h-auto py-2"
              >
                <div className="flex items-center gap-2">
                  {currentStrategyData && (
                    <>
                      <currentStrategyData.icon className={cn("h-4 w-4", currentStrategyData.color)} />
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
                    </>
                  )}
                </div>
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-full p-0" align="start">
              <Command>
                <CommandInput placeholder="Search parsing strategy..." />
                <CommandList>
                  <CommandEmpty>No strategy found.</CommandEmpty>
                  <CommandGroup>
                    {strategies.map((strategy) => {
                      const Icon = strategy.icon;
                      return (
                        <CommandItem
                          key={strategy.value}
                          value={strategy.value}
                          onSelect={(value) => {
                            handleStrategyChange(value as ParsingStrategy);
                            setOpen(false);
                          }}
                          className="flex items-center gap-2 py-3"
                        >
                          <Icon className={cn("h-4 w-4", strategy.color)} />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{strategy.label}</span>
                              {strategy.badge && (
                                <Badge variant={strategy.badgeVariant} className="text-xs h-5">
                                  {strategy.badge}
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">{strategy.subtitle}</p>
                          </div>
                          <Check
                            className={cn(
                              "ml-auto h-4 w-4",
                              currentStrategy === strategy.value ? "opacity-100" : "opacity-0"
                            )}
                          />
                        </CommandItem>
                      );
                    })}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          {/* Strategy Description */}
          {currentStrategyData && (
            <div className={cn(
              "text-xs text-muted-foreground p-3 rounded-md border",
              currentStrategy === 'remote_ocr' || currentStrategy === 'mineru'
                ? "bg-primary/5 border-primary/10"
                : currentStrategy === 'camelot' || currentStrategy === 'dolphin'
                ? "bg-accent/5 border-accent/10"
                : "bg-muted border-muted"
            )}>
              <p className={cn(
                "font-semibold mb-1",
                currentStrategy === 'remote_ocr' || currentStrategy === 'mineru'
                  ? "text-primary"
                  : currentStrategy === 'camelot' || currentStrategy === 'dolphin'
                  ? "text-accent"
                  : ""
              )}>
                {currentStrategyData.description}
              </p>
              <p>{currentStrategyData.details}</p>
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
                  onValueChange={(value) => updateOption('remote_ocr_engine', value as 'tesseract' | 'paddleocr' | 'dolphin')}
                  className="space-y-2"
                >
                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="paddleocr" id="ocr-paddle" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="ocr-paddle" className="flex items-center gap-2 cursor-pointer">
                        <span className="font-semibold">PaddleOCR</span>
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
                        <span className="font-semibold">Tesseract</span>
                        <Badge variant="secondary" className="text-xs">⚡ Fast</Badge>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Fast OCR for simple documents (~0.2s)
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="dolphin" id="ocr-dolphin" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="ocr-dolphin" className="flex items-center gap-2 cursor-pointer">
                        <span className="font-semibold">Dolphin AI</span>
                        <Badge variant="outline" className="text-xs">🤖 AI</Badge>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        AI-powered OCR with highest accuracy (~5s)
                      </p>
                    </div>
                  </div>
                </RadioGroup>
              </div>

              <div className="space-y-2">
                <Label>Languages</Label>
                <div className="flex gap-2 flex-wrap">
                  <Badge variant="default">Korean (한국어)</Badge>
                  <Badge variant="secondary">English</Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Automatically detects Korean and English text
                </p>
              </div>

              <div className="bg-muted/50 p-3 rounded-md border">
                <p className="text-xs font-semibold mb-1">📡 Remote Server</p>
                <p className="text-xs text-muted-foreground">
                  OCR processing is done on remote server (kca-ai.kro.kr:8005)
                </p>
              </div>
            </>
          )}

          {/* Dolphin-specific options */}
          {currentStrategy === 'dolphin' && (
            <>
              <div className="space-y-3">
                <Label>Parsing Level</Label>
                <RadioGroup
                  value={options.dolphin_parsing_level || 'page'}
                  onValueChange={(value) => updateOption('dolphin_parsing_level', value as 'page' | 'element' | 'layout')}
                  className="space-y-2"
                >
                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="page" id="dolphin-page" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="dolphin-page" className="flex items-center gap-2 cursor-pointer">
                        <span className="font-semibold">Page-level</span>
                        <Badge variant="default" className="text-xs">⭐ Recommended</Badge>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Balanced speed & accuracy for most documents
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="element" id="dolphin-element" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="dolphin-element" className="cursor-pointer">
                        <span className="font-semibold">Element-level</span>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Detailed granular element parsing
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="layout" id="dolphin-layout" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="dolphin-layout" className="cursor-pointer">
                        <span className="font-semibold">Layout-level</span>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Focus on document structure and layout analysis
                      </p>
                    </div>
                  </div>
                </RadioGroup>
              </div>

              <div className="space-y-3">
                <Label>GPU Batch Size</Label>
                <RadioGroup
                  value={String(options.dolphin_max_batch_size || 8)}
                  onValueChange={(value) => updateOption('dolphin_max_batch_size', Number(value))}
                  className="space-y-2"
                >
                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="4" id="batch-4" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="batch-4" className="cursor-pointer">
                        <span className="font-semibold">4 pages/batch</span>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Conservative - Lower GPU memory usage
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="8" id="batch-8" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="batch-8" className="flex items-center gap-2 cursor-pointer">
                        <span className="font-semibold">8 pages/batch</span>
                        <Badge variant="default" className="text-xs">⭐ Recommended</Badge>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Optimal performance and GPU memory balance
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="16" id="batch-16" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="batch-16" className="cursor-pointer">
                        <span className="font-semibold">16 pages/batch</span>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Aggressive - High GPU memory, fastest processing
                      </p>
                    </div>
                  </div>
                </RadioGroup>
              </div>

              <div className="bg-muted/50 p-3 rounded-md border">
                <p className="text-xs font-semibold mb-1 flex items-center gap-2">
                  <span className="inline-block w-2 h-2 rounded-full bg-green-500"></span>
                  Remote GPU Server
                </p>
                <p className="text-xs text-muted-foreground">
                  Processing is done on remote GPU server for maximum performance
                </p>
              </div>
            </>
          )}

          {/* MinerU-specific options */}
          {currentStrategy === 'mineru' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="mineru-lang">Language</Label>
                <Select
                  value={options.mineru_lang || 'auto'}
                  onValueChange={(value) => updateOption('mineru_lang', value as 'auto' | 'ko' | 'zh' | 'en' | 'ja')}
                >
                  <SelectTrigger id="mineru-lang">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto-detect</SelectItem>
                    <SelectItem value="ko">Korean (한국어)</SelectItem>
                    <SelectItem value="zh">Chinese (中文)</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="ja">Japanese (日本語)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  MinerU supports 84 languages with automatic detection
                </p>
              </div>

              <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="mineru-ocr" className="cursor-pointer font-semibold">Enable OCR</Label>
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
            </>
          )}

          {/* Camelot-specific options */}
          {currentStrategy === 'camelot' && (
            <>
              <div className="space-y-3">
                <Label>Table Extraction Mode</Label>
                <RadioGroup
                  value={options.camelot_mode || 'hybrid'}
                  onValueChange={(value) => updateOption('camelot_mode', value as 'lattice' | 'stream' | 'hybrid')}
                  className="space-y-2"
                >
                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="hybrid" id="camelot-hybrid" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="camelot-hybrid" className="flex items-center gap-2 cursor-pointer">
                        <span className="font-semibold">Hybrid</span>
                        <Badge variant="default" className="text-xs">⭐ Recommended</Badge>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Combines lattice and stream for best results
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="lattice" id="camelot-lattice" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="camelot-lattice" className="cursor-pointer">
                        <span className="font-semibold">Lattice</span>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Grid-based detection for bordered tables
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                    <RadioGroupItem value="stream" id="camelot-stream" className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor="camelot-stream" className="cursor-pointer">
                        <span className="font-semibold">Stream</span>
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        Text-based detection for borderless tables
                      </p>
                    </div>
                  </div>
                </RadioGroup>
              </div>

              <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="ocr-switch" className="cursor-pointer font-semibold">Enable OCR</Label>
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

              {/* OCR Engine Selection (only shown when OCR is enabled) */}
              {options.do_ocr && (
                <div className="space-y-3">
                  <Label>OCR Engine (Local)</Label>
                  <RadioGroup
                    value={options.ocr_engine || 'easyocr'}
                    onValueChange={(value) => updateOption('ocr_engine', value as 'easyocr' | 'tesseract')}
                    className="space-y-2"
                  >
                    <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                      <RadioGroupItem value="easyocr" id="camelot-ocr-easy" className="mt-1" />
                      <div className="flex-1">
                        <Label htmlFor="camelot-ocr-easy" className="flex items-center gap-2 cursor-pointer">
                          <span className="font-semibold">EasyOCR</span>
                          <Badge variant="default" className="text-xs">⭐ Recommended</Badge>
                        </Label>
                        <p className="text-sm text-muted-foreground mt-1">
                          High accuracy for Korean & English (Python-based)
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                      <RadioGroupItem value="tesseract" id="camelot-ocr-tess" className="mt-1" />
                      <div className="flex-1">
                        <Label htmlFor="camelot-ocr-tess" className="cursor-pointer">
                          <span className="font-semibold">Tesseract</span>
                        </Label>
                        <p className="text-sm text-muted-foreground mt-1">
                          Fast processing, good for simple documents
                        </p>
                      </div>
                    </div>
                  </RadioGroup>
                </div>
              )}
            </>
          )}

          {/* Docling-specific options */}
          {currentStrategy === 'docling' && (
            <>
              <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="docling-ocr" className="cursor-pointer font-semibold">Enable OCR</Label>
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

              {/* OCR Engine Selection (only shown when OCR is enabled) */}
              {options.do_ocr && (
                <div className="space-y-3">
                  <Label>OCR Engine (Local)</Label>
                  <RadioGroup
                    value={options.ocr_engine || 'easyocr'}
                    onValueChange={(value) => updateOption('ocr_engine', value as 'easyocr' | 'tesseract')}
                    className="space-y-2"
                  >
                    <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                      <RadioGroupItem value="easyocr" id="docling-ocr-easy" className="mt-1" />
                      <div className="flex-1">
                        <Label htmlFor="docling-ocr-easy" className="flex items-center gap-2 cursor-pointer">
                          <span className="font-semibold">EasyOCR</span>
                          <Badge variant="default" className="text-xs">⭐ Recommended</Badge>
                        </Label>
                        <p className="text-sm text-muted-foreground mt-1">
                          High accuracy for Korean & English (Python-based)
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-lg border p-4 hover:bg-accent/5 transition-colors">
                      <RadioGroupItem value="tesseract" id="docling-ocr-tess" className="mt-1" />
                      <div className="flex-1">
                        <Label htmlFor="docling-ocr-tess" className="cursor-pointer">
                          <span className="font-semibold">Tesseract</span>
                        </Label>
                        <p className="text-sm text-muted-foreground mt-1">
                          Fast processing, good for simple documents
                        </p>
                      </div>
                    </div>
                  </RadioGroup>
                </div>
              )}
            </>
          )}

          {/* Common Options */}
          <div className="pt-6 border-t space-y-6">
            <div className="space-y-3">
              <Label>Output Format</Label>
              <RadioGroup
                value={options.output_format || 'markdown'}
                onValueChange={(value) => updateOption('output_format', value as 'markdown' | 'html' | 'json')}
                className="grid grid-cols-3 gap-2"
              >
                <div className="relative">
                  <RadioGroupItem value="markdown" id="format-md" className="peer sr-only" />
                  <Label
                    htmlFor="format-md"
                    className="flex flex-col items-center justify-center rounded-lg border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5 cursor-pointer transition-colors"
                  >
                    <FileText className="mb-2 h-5 w-5" />
                    <span className="text-sm font-semibold">Markdown</span>
                  </Label>
                </div>

                <div className="relative">
                  <RadioGroupItem value="html" id="format-html" className="peer sr-only" />
                  <Label
                    htmlFor="format-html"
                    className="flex flex-col items-center justify-center rounded-lg border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5 cursor-pointer transition-colors"
                  >
                    <FileText className="mb-2 h-5 w-5" />
                    <span className="text-sm font-semibold">HTML</span>
                  </Label>
                </div>

                <div className="relative">
                  <RadioGroupItem value="json" id="format-json" className="peer sr-only" />
                  <Label
                    htmlFor="format-json"
                    className="flex flex-col items-center justify-center rounded-lg border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5 cursor-pointer transition-colors"
                  >
                    <FileText className="mb-2 h-5 w-5" />
                    <span className="text-sm font-semibold">JSON</span>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/5 transition-colors">
              <div className="space-y-0.5 flex-1">
                <Label htmlFor="extract-tables" className="cursor-pointer font-semibold">Extract Tables</Label>
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
                <Label htmlFor="save-output" className="cursor-pointer font-semibold">Save to Output Folder</Label>
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
