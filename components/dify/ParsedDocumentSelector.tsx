'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Search, FileText, Calendar, HardDrive, X, ChevronLeft, ChevronRight, Table2, Image, FileCheck, Layers } from 'lucide-react'
import type { ParsedDocument } from '@/lib/types'

interface ParsedDocumentSelectorProps {
  documents: ParsedDocument[]
  selectedDocs: string[]
  onChange: (docPaths: string[]) => void
  loading?: boolean
}

export function ParsedDocumentSelector({
  documents,
  selectedDocs,
  onChange,
  loading
}: ParsedDocumentSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 6

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getParserBadgeColor = (strategy?: string) => {
    if (!strategy) return 'default'
    const s = strategy.toLowerCase()
    if (s.includes('dolphin')) return 'default'
    if (s.includes('mineru')) return 'secondary'
    if (s.includes('remote') && s.includes('ocr')) return 'secondary'
    return 'outline'
  }

  // Filter documents based on search query (by original filename only)
  const filteredDocuments = useMemo(() => {
    if (!searchQuery.trim()) return documents

    const query = searchQuery.toLowerCase()
    return documents.filter(
      (doc) =>
        doc.filename && doc.filename.toLowerCase().includes(query)
    )
  }, [documents, searchQuery])

  // Pagination
  const totalPages = Math.ceil(filteredDocuments.length / itemsPerPage)
  const paginatedDocuments = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage
    return filteredDocuments.slice(start, start + itemsPerPage)
  }, [filteredDocuments, currentPage, itemsPerPage])

  // Get selected document objects
  const selectedDocuments = useMemo(() => {
    return documents.filter(doc => selectedDocs.includes(doc.path))
  }, [documents, selectedDocs])

  // Toggle document selection
  const toggleDocument = (docPath: string) => {
    if (selectedDocs.includes(docPath)) {
      onChange(selectedDocs.filter(path => path !== docPath))
    } else {
      onChange([...selectedDocs, docPath])
    }
  }

  // Remove selected document
  const removeDocument = (docPath: string) => {
    onChange(selectedDocs.filter(path => path !== docPath))
  }

  // Reset page when search changes
  useMemo(() => {
    setCurrentPage(1)
  }, [searchQuery])

  return (
    <Card className="gap-3 py-4">
      <CardHeader className="pb-0 px-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <FileText className="h-4 w-4" />
          Parsed Documents
          <span className="text-xs font-normal text-muted-foreground ml-auto">
            {selectedDocs.length} selected • {filteredDocuments.length} of {documents.length}
          </span>
        </CardTitle>
        <CardDescription className="text-xs">
          Select documents to upload to Dify Knowledge Base (showing original filenames)
        </CardDescription>
      </CardHeader>
      <CardContent className="px-4">
        {loading ? (
          <div className="text-sm text-muted-foreground">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No parsed documents found.</p>
            <p className="text-xs mt-1">Parse a document first to upload to Dify.</p>
          </div>
        ) : (
          <>
            {/* Selected Documents */}
            {selectedDocuments.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3 p-3 rounded-lg bg-accent/30 border">
                {selectedDocuments.map((doc) => (
                  <Badge key={doc.path} variant="secondary" className="gap-1">
                    {doc.filename}
                    <button
                      onClick={() => removeDocument(doc.path)}
                      className="ml-1 hover:bg-accent rounded-sm"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}

            {/* Search Bar */}
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by original filename..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Document List Grid */}
            {filteredDocuments.length === 0 ? (
              <div className="text-center py-6 text-muted-foreground">
                <p className="text-sm">No documents match your search.</p>
              </div>
            ) : (
              <>
                <div className="space-y-2 mb-4">
                  {paginatedDocuments.map((doc) => {
                    const isSelected = selectedDocs.includes(doc.path)
                    return (
                      <Label
                        key={doc.path}
                        htmlFor={doc.path}
                        className={`flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition-all hover:border-primary hover:bg-accent/50 ${
                          isSelected ? 'border-primary bg-accent/30' : ''
                        }`}
                      >
                        <Checkbox
                          id={doc.path}
                          checked={isSelected}
                          onCheckedChange={() => toggleDocument(doc.path)}
                        />
                        <div className="flex-1 min-w-0 space-y-2">
                          {/* Title: Original filename (NOT content.md) */}
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm truncate flex-1" title={doc.filename}>
                              {doc.filename}
                            </span>
                            {doc.parsing_strategy && (
                              <Badge variant={getParserBadgeColor(doc.parsing_strategy) as any} className="text-xs">
                                {doc.parsing_strategy}
                              </Badge>
                            )}
                          </div>

                          {/* Metadata badges */}
                          <div className="flex flex-wrap gap-2">
                            {doc.total_pages && (
                              <Badge variant="secondary" className="gap-1 text-xs">
                                <FileCheck className="h-3 w-3" />
                                {doc.total_pages} {doc.total_pages === 1 ? 'page' : 'pages'}
                              </Badge>
                            )}
                            {doc.chunk_count > 0 && (
                              <Badge variant="outline" className="gap-1 text-xs">
                                <Layers className="h-3 w-3" />
                                {doc.chunk_count} chunks
                              </Badge>
                            )}
                            {doc.table_count > 0 && (
                              <Badge variant="outline" className="gap-1 text-xs">
                                <Table2 className="h-3 w-3" />
                                {doc.table_count}
                              </Badge>
                            )}
                            {doc.picture_count > 0 && (
                              <Badge variant="outline" className="gap-1 text-xs">
                                <Image className="h-3 w-3" />
                                {doc.picture_count}
                              </Badge>
                            )}
                          </div>

                          {/* File info */}
                          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <HardDrive className="h-3 w-3" />
                              {formatBytes(doc.size)}
                            </span>
                            {doc.file_size && (
                              <span className="flex items-center gap-1">
                                Original: {formatBytes(doc.file_size)}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(doc.last_parsed_at || doc.created_at)}
                            </span>
                          </div>
                        </div>
                      </Label>
                    )
                  })}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
