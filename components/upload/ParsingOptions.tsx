'use client';

import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ParseOptions } from '@/lib/types';
import { Sparkles, Zap, FileText } from 'lucide-react';

interface ParsingOptionsProps {
  options: ParseOptions;
  onOptionsChange: (options: ParseOptions) => void;
}

type ParsingStrategy = 'mineru' | 'camelot' | 'docling';

export function ParsingOptions({ options, onOptionsChange }: ParsingOptionsProps) {
  const updateOption = <K extends keyof ParseOptions>(key: K, value: ParseOptions[K]) => {
    onOptionsChange({ ...options, [key]: value });
  };

  // Determine current strategy based on options
  const getCurrentStrategy = (): ParsingStrategy => {
    if (options.use_mineru) return 'mineru';
    if (options.use_camelot !== false) return 'camelot'; // Default
    return 'docling';
  };

  const currentStrategy = getCurrentStrategy();

  const handleStrategyChange = (strategy: ParsingStrategy) => {
    const newOptions = { ...options };

    // Reset strategy flags
    newOptions.use_mineru = false;
    newOptions.use_camelot = false;

    // Set selected strategy
    if (strategy === 'mineru') {
      newOptions.use_mineru = true;
      newOptions.mineru_lang = newOptions.mineru_lang || 'auto';
      newOptions.mineru_use_ocr = newOptions.mineru_use_ocr ?? true;
    } else if (strategy === 'camelot') {
      newOptions.use_camelot = true;
      newOptions.camelot_mode = newOptions.camelot_mode || 'hybrid';
    }
    // docling: both false (default Docling behavior)

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
            <Badge variant="default" className="ml-auto">MinerU Default</Badge>
          </CardTitle>
          <CardDescription>
            Choose the parsing engine for your document (MinerU recommended for best results)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Select
            value={currentStrategy}
            onValueChange={(value) => handleStrategyChange(value as ParsingStrategy)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select parsing strategy" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="mineru">
                <div className="flex items-center gap-2 w-full">
                  <Sparkles className="h-4 w-4 text-primary flex-shrink-0" />
                  <span className="flex-1">MinerU (Universal)</span>
                  <Badge variant="secondary" className="text-xs">Recommended</Badge>
                </div>
              </SelectItem>
              <SelectItem value="camelot">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-accent" />
                  <span>Camelot + Docling (Hybrid)</span>
                </div>
              </SelectItem>
              <SelectItem value="docling">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span>Docling Only (Basic)</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>

          {/* Strategy Description */}
          {currentStrategy === 'mineru' && (
            <div className="text-xs text-muted-foreground bg-primary/5 p-3 rounded-md border border-primary/10">
              <p className="font-semibold text-primary mb-1">Universal PDF Parser</p>
              <p>Advanced features: merged cells, hierarchical tables, automatic text ordering, 84 languages support</p>
            </div>
          )}
          {currentStrategy === 'camelot' && (
            <div className="text-xs text-muted-foreground bg-accent/5 p-3 rounded-md border border-accent/10">
              <p className="font-semibold text-accent mb-1">High-Accuracy Table Extraction</p>
              <p>Best for PDFs with complex tables. Combines Camelot (tables) + Docling (text)</p>
            </div>
          )}
          {currentStrategy === 'docling' && (
            <div className="text-xs text-muted-foreground bg-muted p-3 rounded-md">
              <p className="font-semibold mb-1">Basic Document Parsing</p>
              <p>Fast parsing for simple documents without advanced table extraction</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Strategy-Specific Options */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Advanced Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* MinerU-specific options */}
          {currentStrategy === 'mineru' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="mineru-lang">Language</Label>
                <Select
                  value={options.mineru_lang || 'auto'}
                  onValueChange={(value) => updateOption('mineru_lang', value as 'auto' | 'ko' | 'ch' | 'en' | 'ja')}
                >
                  <SelectTrigger id="mineru-lang">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto-detect</SelectItem>
                    <SelectItem value="ko">Korean (한국어)</SelectItem>
                    <SelectItem value="ch">Chinese (中文)</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="ja">Japanese (日本語)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  MinerU supports 84 languages with automatic detection
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="mineru-ocr">Enable OCR</Label>
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
              <div className="space-y-2">
                <Label htmlFor="camelot-mode">Table Extraction Mode</Label>
                <Select
                  value={options.camelot_mode || 'hybrid'}
                  onValueChange={(value) => updateOption('camelot_mode', value as 'lattice' | 'stream' | 'hybrid')}
                >
                  <SelectTrigger id="camelot-mode">
                    <SelectValue placeholder="Select table mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hybrid">Hybrid (Recommended)</SelectItem>
                    <SelectItem value="lattice">Lattice (Grid-based)</SelectItem>
                    <SelectItem value="stream">Stream (Text-based)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Hybrid combines lattice and stream for best results
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="ocr-switch">Enable OCR</Label>
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
            </>
          )}

          {/* Docling-specific options */}
          {currentStrategy === 'docling' && (
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="docling-ocr">Enable OCR</Label>
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
          )}

          {/* Common Options */}
          <div className="pt-4 border-t space-y-6">
            <div className="space-y-2">
              <Label htmlFor="output-format">Output Format</Label>
              <Select
                value={options.output_format || 'markdown'}
                onValueChange={(value) => updateOption('output_format', value as 'markdown' | 'html' | 'json')}
              >
                <SelectTrigger id="output-format">
                  <SelectValue placeholder="Select output format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="markdown">Markdown</SelectItem>
                  <SelectItem value="html">HTML</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="extract-tables">Extract Tables</Label>
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

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="save-output">Save to Output Folder</Label>
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
      </Card>
    </div>
  );
}
