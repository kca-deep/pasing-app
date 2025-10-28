'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Download, FileText, Table2, Zap, Sparkles, ScanText } from 'lucide-react';
import type { ParseResponse } from '@/lib/types';

interface MetadataPanelProps {
  result: ParseResponse;
  filename: string;
  className?: string;
}

export function MetadataPanel({ result, filename, className }: MetadataPanelProps) {
  const handleDownload = () => {
    if (!result.markdown) return;

    const blob = new Blob([result.markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename.replace(/\.[^/.]+$/, '')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Document Info
        </CardTitle>
        <CardDescription>{filename}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Document Statistics */}
        {result.stats && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Statistics</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-muted-foreground">Lines</p>
                <p className="font-medium">{result.stats.lines.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Words</p>
                <p className="font-medium">{result.stats.words.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Characters</p>
                <p className="font-medium">{result.stats.characters.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Size</p>
                <p className="font-medium">{result.stats.size_kb} KB</p>
              </div>
            </div>
          </div>
        )}

        <Separator />

        {/* Table Summary */}
        {result.table_summary && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <Table2 className="h-4 w-4" />
              Tables
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Total Tables</span>
                <Badge variant="secondary">
                  {result.table_summary.total_tables}
                </Badge>
              </div>
              {result.table_summary.markdown_tables > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Markdown</span>
                  <Badge variant="outline">
                    {result.table_summary.markdown_tables}
                  </Badge>
                </div>
              )}
              {result.table_summary.json_tables > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">JSON (Complex)</span>
                  <Badge variant="outline">
                    {result.table_summary.json_tables}
                  </Badge>
                </div>
              )}
              {result.table_summary.parsing_method === 'mineru' && (
                <>
                  {result.table_summary.language && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Language</span>
                      <Badge variant="outline">
                        {result.table_summary.language === 'ko' ? '한국어 (Korean)' :
                         result.table_summary.language === 'zh' ? '中文 (Chinese)' :
                         result.table_summary.language === 'en' ? 'English' :
                         result.table_summary.language === 'ja' ? '日本語 (Japanese)' :
                         result.table_summary.language === 'auto' ? 'Auto-detect' :
                         result.table_summary.language}
                      </Badge>
                    </div>
                  )}
                  {result.table_summary.total_images !== undefined && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Images</span>
                      <Badge variant="outline">
                        {result.table_summary.total_images}
                      </Badge>
                    </div>
                  )}
                  {result.table_summary.total_formulas !== undefined && result.table_summary.total_formulas > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Formulas</span>
                      <Badge variant="outline">
                        {result.table_summary.total_formulas}
                      </Badge>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        <Separator />

        {/* Parsing Metadata */}
        {result.parsing_metadata && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Parsing Configuration</h4>
            <div className="space-y-2">
              {/* Main Parser */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Parser</span>
                <Badge variant={
                  result.parsing_metadata.parser_used === 'dolphin' || result.parsing_metadata.parser_used === 'dolphin_remote' ? 'default' :
                  result.parsing_metadata.parser_used === 'mineru' ? 'secondary' :
                  'outline'
                } className="gap-1">
                  {(result.parsing_metadata.parser_used === 'dolphin' || result.parsing_metadata.parser_used === 'dolphin_remote') && (
                    <>
                      <Zap className="h-3 w-3" />
                      Dolphin (AI)
                    </>
                  )}
                  {result.parsing_metadata.parser_used === 'mineru' && (
                    <>
                      <Sparkles className="h-3 w-3" />
                      MinerU
                    </>
                  )}
                  {result.parsing_metadata.parser_used === 'docling' && (
                    <>
                      <FileText className="h-3 w-3" />
                      Docling
                    </>
                  )}
                  {result.parsing_metadata.parser_used === 'remote_ocr' && (
                    <>
                      <ScanText className="h-3 w-3" />
                      Remote OCR
                    </>
                  )}
                  {result.parsing_metadata.parser_used === 'camelot' && (
                    <>
                      <Zap className="h-3 w-3" />
                      Camelot
                    </>
                  )}
                  {!['dolphin', 'dolphin_remote', 'mineru', 'docling', 'remote_ocr', 'camelot'].includes(result.parsing_metadata.parser_used) && result.parsing_metadata.parser_used}
                </Badge>
              </div>

              {/* Table Parser */}
              {result.parsing_metadata.table_parser &&
               result.parsing_metadata.table_parser !== result.parsing_metadata.parser_used && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Table Parser</span>
                  <Badge variant="outline" className="gap-1">
                    {result.parsing_metadata.table_parser === 'camelot' && (
                      <>
                        <Zap className="h-3 w-3" />
                        Camelot
                      </>
                    )}
                    {result.parsing_metadata.table_parser === 'docling' && (
                      <>
                        <FileText className="h-3 w-3" />
                        Docling
                      </>
                    )}
                    {result.parsing_metadata.table_parser === 'mineru' && (
                      <>
                        <Sparkles className="h-3 w-3" />
                        MinerU
                      </>
                    )}
                  </Badge>
                </div>
              )}

              {/* OCR Status */}
              {result.parsing_metadata.ocr_enabled && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">OCR</span>
                  <Badge variant="secondary">Enabled</Badge>
                </div>
              )}

              {/* Camelot Mode */}
              {result.parsing_metadata.camelot_mode && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Camelot Mode</span>
                  <Badge variant="outline">
                    {result.parsing_metadata.camelot_mode}
                  </Badge>
                </div>
              )}

              {/* Dolphin Parsing Level */}
              {result.parsing_metadata.dolphin_parsing_level && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Parsing Level</span>
                  <Badge variant="outline">
                    {result.parsing_metadata.dolphin_parsing_level}
                  </Badge>
                </div>
              )}

              {/* MinerU Language */}
              {result.parsing_metadata.mineru_lang && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Language</span>
                  <Badge variant="outline">
                    {result.parsing_metadata.mineru_lang === 'ko' && '🇰🇷 Korean'}
                    {result.parsing_metadata.mineru_lang === 'zh' && '🇨🇳 Chinese'}
                    {result.parsing_metadata.mineru_lang === 'en' && '🇺🇸 English'}
                    {result.parsing_metadata.mineru_lang === 'ja' && '🇯🇵 Japanese'}
                    {result.parsing_metadata.mineru_lang === 'auto' && '🌐 Auto'}
                  </Badge>
                </div>
              )}

              {/* Picture Description */}
              {result.parsing_metadata.picture_description_enabled && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Picture Description</span>
                  <Badge variant="secondary">VLM Enabled</Badge>
                </div>
              )}

              {/* Auto Image Analysis */}
              {result.parsing_metadata.auto_image_analysis_enabled && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Auto Image Analysis</span>
                  <Badge variant="secondary">Smart Detection</Badge>
                </div>
              )}

              {/* Output Format */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Output Format</span>
                <Badge variant="outline">
                  {result.parsing_metadata.output_format.toUpperCase()}
                </Badge>
              </div>
            </div>
          </div>
        )}

        <Separator />

        {/* Output Information */}
        {result.output_structure && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Output Files</h4>
            <div className="text-xs text-muted-foreground space-y-1">
              <p>📁 {result.output_structure.output_dir}</p>
              {result.output_structure.tables_dir && (
                <p>📁 {result.output_structure.tables_dir}</p>
              )}
            </div>
          </div>
        )}

        <Separator />

        {/* Download Button */}
        <Button
          className="w-full"
          variant="outline"
          onClick={handleDownload}
          disabled={!result.markdown}
        >
          <Download className="mr-2 h-4 w-4" />
          Download Markdown
        </Button>
      </CardContent>
    </Card>
  );
}
