'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { TableViewer } from './TableViewer';
import { TableData } from '@/lib/types';
import { Download, Copy, Check } from 'lucide-react';

interface TableDetailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tableData: TableData | null;
}

export function TableDetailModal({
  open,
  onOpenChange,
  tableData,
}: TableDetailModalProps) {
  const [copied, setCopied] = useState(false);

  if (!tableData) return null;

  const { table_id, caption, complexity, summary } = tableData;

  // Convert table to CSV format
  const tableToCSV = (): string => {
    const csvRows: string[] = [];

    // Add headers
    if (tableData.structure.headers && tableData.structure.headers.length > 0) {
      tableData.structure.headers.forEach(headerRow => {
        csvRows.push(headerRow.map(cell => `"${cell}"`).join(','));
      });
    }

    // Add data rows
    if (tableData.structure.rows && tableData.structure.rows.length > 0) {
      tableData.structure.rows.forEach(row => {
        csvRows.push(row.map(cell => `"${cell}"`).join(','));
      });
    }

    return csvRows.join('\n');
  };

  // Download as JSON
  const handleDownloadJSON = () => {
    const blob = new Blob([JSON.stringify(tableData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${table_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Download as CSV
  const handleDownloadCSV = () => {
    const csv = tableToCSV();
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${table_id}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Copy to clipboard
  const handleCopy = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <DialogTitle className="text-foreground">
                {caption || `Table ${table_id}`}
              </DialogTitle>
              <DialogDescription>
                Page {tableData.page} • {complexity.rows} rows × {complexity.cols}{' '}
                columns
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              {complexity.is_complex && (
                <Badge variant="destructive">Complex</Badge>
              )}
              {complexity.has_merged_cells && (
                <Badge variant="outline">Merged Cells</Badge>
              )}
            </div>
          </div>
          {summary && (
            <div className="pt-4 border-t border-border">
              <p className="text-sm font-medium text-foreground mb-2">
                AI Summary
              </p>
              <p className="text-sm text-muted-foreground">{summary}</p>
            </div>
          )}
        </DialogHeader>

        <Tabs defaultValue="preview" className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="json">JSON</TabsTrigger>
            <TabsTrigger value="csv">CSV</TabsTrigger>
          </TabsList>

          <TabsContent value="preview" className="flex-1 overflow-hidden mt-4">
            <ScrollArea className="h-full">
              <TableViewer tableData={tableData} />
            </ScrollArea>
          </TabsContent>

          <TabsContent value="json" className="flex-1 overflow-hidden mt-4">
            <div className="space-y-2">
              <div className="flex gap-2">
                <Button
                  onClick={handleDownloadJSON}
                  variant="outline"
                  size="sm"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download JSON
                </Button>
                <Button
                  onClick={() => handleCopy(JSON.stringify(tableData, null, 2))}
                  variant="outline"
                  size="sm"
                >
                  {copied ? (
                    <Check className="mr-2 h-4 w-4" />
                  ) : (
                    <Copy className="mr-2 h-4 w-4" />
                  )}
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>
              <ScrollArea className="h-[400px] w-full rounded-md border border-border">
                <pre className="p-4 text-sm text-foreground">
                  <code>{JSON.stringify(tableData, null, 2)}</code>
                </pre>
              </ScrollArea>
            </div>
          </TabsContent>

          <TabsContent value="csv" className="flex-1 overflow-hidden mt-4">
            <div className="space-y-2">
              <div className="flex gap-2">
                <Button
                  onClick={handleDownloadCSV}
                  variant="outline"
                  size="sm"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download CSV
                </Button>
                <Button
                  onClick={() => handleCopy(tableToCSV())}
                  variant="outline"
                  size="sm"
                >
                  {copied ? (
                    <Check className="mr-2 h-4 w-4" />
                  ) : (
                    <Copy className="mr-2 h-4 w-4" />
                  )}
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>
              <ScrollArea className="h-[400px] w-full rounded-md border border-border">
                <pre className="p-4 text-sm text-foreground whitespace-pre-wrap">
                  <code>{tableToCSV()}</code>
                </pre>
              </ScrollArea>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
