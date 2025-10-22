'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TableData } from '@/lib/types';
import { FileSpreadsheet, Eye } from 'lucide-react';

interface TableSummaryProps {
  tableData: TableData;
  onViewDetails?: () => void;
}

export function TableSummary({ tableData, onViewDetails }: TableSummaryProps) {
  const { table_id, caption, complexity, summary, page } = tableData;

  return (
    <Card className="border-border bg-card hover:bg-accent/5 transition-colors">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <FileSpreadsheet className="h-5 w-5 text-primary" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-card-foreground">
                {caption || `Table ${table_id}`}
              </CardTitle>
              <CardDescription>
                Page {page} • {complexity.rows} rows × {complexity.cols} columns
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {complexity.is_complex && (
              <Badge variant="destructive">Complex</Badge>
            )}
            {complexity.has_merged_cells && (
              <Badge variant="outline">Merged</Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {summary ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">AI Summary</p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {summary}
            </p>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground italic">
            No summary available for this table
          </p>
        )}
        {onViewDetails && (
          <Button
            onClick={onViewDetails}
            variant="outline"
            size="sm"
            className="w-full"
          >
            <Eye className="mr-2 h-4 w-4" />
            View Full Table
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
