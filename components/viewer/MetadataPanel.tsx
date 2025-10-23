'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Download, FileText, Table2 } from 'lucide-react';
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
