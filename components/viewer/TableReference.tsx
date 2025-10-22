'use client';

import React, { useState, useEffect } from 'react';
import { TableSummary } from './TableSummary';
import { TableDetailModal } from './TableDetailModal';
import { TableData } from '@/lib/types';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

interface TableReferenceProps {
  tableId: string;
  docName: string;
}

export function TableReference({ tableId, docName }: TableReferenceProps) {
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    const loadTableData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `/api/tables/${tableId}?doc=${encodeURIComponent(docName)}`
        );

        if (!response.ok) {
          throw new Error('Failed to load table data');
        }

        const data = await response.json();
        setTableData(data);
      } catch (err: any) {
        console.error('Error loading table:', err);
        setError(err.message || 'Failed to load table');
      } finally {
        setLoading(false);
      }
    };

    loadTableData();
  }, [tableId, docName]);

  if (loading) {
    return (
      <div className="my-6">
        <div className="border border-border rounded-lg p-6 bg-muted/20 animate-pulse">
          <div className="h-4 bg-muted rounded w-1/3 mb-2"></div>
          <div className="h-3 bg-muted rounded w-1/4 mb-4"></div>
          <div className="h-20 bg-muted rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !tableData) {
    return (
      <div className="my-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Table data not available'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="my-6 not-prose">
      <TableSummary
        tableData={tableData}
        onViewDetails={() => setModalOpen(true)}
      />
      <TableDetailModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        tableData={tableData}
      />
    </div>
  );
}
