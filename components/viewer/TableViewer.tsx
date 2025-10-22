'use client';

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TableData } from '@/lib/types';

interface TableViewerProps {
  tableData: TableData;
  compact?: boolean;
}

export function TableViewer({ tableData, compact = false }: TableViewerProps) {
  const { structure, caption, complexity, page } = tableData;

  // Render table headers
  const renderHeaders = () => {
    if (!structure.headers || structure.headers.length === 0) {
      return null;
    }

    return (
      <TableHeader>
        {structure.headers.map((headerRow, rowIndex) => (
          <TableRow key={`header-${rowIndex}`}>
            {headerRow.map((cell, cellIndex) => (
              <TableHead
                key={`header-${rowIndex}-${cellIndex}`}
                className="border-border bg-muted/50 font-semibold"
              >
                {cell || '-'}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
    );
  };

  // Render table rows
  const renderRows = () => {
    if (!structure.rows || structure.rows.length === 0) {
      return (
        <TableRow>
          <TableCell colSpan={100} className="text-center text-muted-foreground">
            No data available
          </TableCell>
        </TableRow>
      );
    }

    // Limit rows in compact mode
    const rowsToShow = compact ? structure.rows.slice(0, 5) : structure.rows;

    return (
      <>
        {rowsToShow.map((row, rowIndex) => (
          <TableRow key={`row-${rowIndex}`}>
            {row.map((cell, cellIndex) => (
              <TableCell
                key={`row-${rowIndex}-${cellIndex}`}
                className="border-border"
              >
                {cell || '-'}
              </TableCell>
            ))}
          </TableRow>
        ))}
        {compact && structure.rows.length > 5 && (
          <TableRow>
            <TableCell
              colSpan={structure.rows[0]?.length || 1}
              className="text-center text-muted-foreground italic"
            >
              ... and {structure.rows.length - 5} more rows
            </TableCell>
          </TableRow>
        )}
      </>
    );
  };

  const complexityBadge = complexity.is_complex ? (
    <Badge variant="destructive">Complex</Badge>
  ) : (
    <Badge variant="secondary">Simple</Badge>
  );

  if (compact) {
    return (
      <div className="space-y-2">
        {caption && (
          <p className="text-sm font-medium text-foreground">{caption}</p>
        )}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Page {page}</span>
          <span>•</span>
          <span>
            {complexity.rows} × {complexity.cols}
          </span>
          {complexityBadge}
        </div>
        <div className="overflow-x-auto">
          <Table>
            {renderHeaders()}
            <TableBody>{renderRows()}</TableBody>
          </Table>
        </div>
      </div>
    );
  }

  return (
    <Card className="border-border">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-card-foreground">
              {caption || `Table ${tableData.table_id}`}
            </CardTitle>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>Page {page}</span>
              <span>•</span>
              <span>
                {complexity.rows} rows × {complexity.cols} columns
              </span>
              {complexity.has_merged_cells && (
                <>
                  <span>•</span>
                  <Badge variant="outline">Merged Cells</Badge>
                </>
              )}
            </div>
          </div>
          {complexityBadge}
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            {renderHeaders()}
            <TableBody>{renderRows()}</TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
