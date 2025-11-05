'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip';
import { FileText, Upload, Clock, Table2, ArrowRight, FileIcon, Sparkles, Zap, ScanText } from 'lucide-react';
import { getParsedDocuments } from '@/lib/api';

interface ParsedDocument {
  id: number;  // Parsing History ID (unique across all versions)
  document_id: number;  // Document ID (same for all versions of same file)
  document_name: string;
  parsed_at: number;
  size_kb: number;
  preview: string;
  table_count: number;
  output_dir: string;
  parsing_metadata?: {
    parser_used: string;
    table_parser?: string;
    ocr_enabled: boolean;
    ocr_engine?: string;
    output_format: string;
    camelot_mode?: string;
    dolphin_parsing_level?: string;
    mineru_lang?: string;
    picture_description_enabled: boolean;
    auto_image_analysis_enabled: boolean;
  };
}

export default function Home() {
  const [documents, setDocuments] = useState<ParsedDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const data = await getParsedDocuments();
        setDocuments(data.documents);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load documents');
      } finally {
        setIsLoading(false);
      }
    };

    loadDocuments();
  }, []);

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const getParserBadge = (parser: string) => {
    switch (parser) {
      case 'dolphin':
      case 'dolphin_remote':
        return { icon: Zap, label: 'Dolphin (AI)', variant: 'default' as const };
      case 'mineru':
        return { icon: Sparkles, label: 'MinerU', variant: 'secondary' as const };
      case 'remote_ocr':
        return { icon: ScanText, label: 'Remote OCR', variant: 'secondary' as const };
      case 'docling':
      default:
        return { icon: FileText, label: 'Docling', variant: 'outline' as const };
    }
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen">
        {/* Hero Section */}
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto mb-8 animate-fade-in-up">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h1 className="text-2xl font-bold mb-1 flex items-center gap-2">
                  Document Parser
                  <Sparkles className="h-5 w-5 text-primary animate-pulse" />
                </h1>
                <p className="text-sm text-muted-foreground">
                  High-accuracy parsing powered by Docling + Camelot
                </p>
              </div>
              <Link href="/parse">
                <Button className="gap-2 transition-all hover:scale-105 hover:shadow-lg">
                  <Upload className="h-4 w-4" />
                  Parse New Document
                </Button>
              </Link>
            </div>
          </div>

        {/* Parsed Documents Section */}
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              Recently Parsed
              {documents.length > 0 && (
                <span className="text-muted-foreground ml-2">({documents.length})</span>
              )}
            </h2>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <Card key={i} className={`animate-scale-in stagger-${i} relative overflow-hidden`}>
                  <div className="absolute inset-0 animate-shimmer pointer-events-none" />
                  <CardHeader>
                    <Skeleton className="h-6 w-3/4 mb-2" />
                    <Skeleton className="h-4 w-1/2" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-16 w-full mb-4" />
                    <div className="flex gap-2 mb-4">
                      <Skeleton className="h-5 w-16" />
                      <Skeleton className="h-5 w-20" />
                    </div>
                    <Skeleton className="h-10 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <Card className="border-destructive animate-scale-in">
              <CardContent className="pt-6">
                <p className="text-destructive">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Empty State */}
          {!isLoading && !error && documents.length === 0 && (
            <Card className="border-dashed animate-fade-in-up">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <div className="relative">
                  <FileText className="h-16 w-16 text-muted-foreground mb-4 animate-pulse" />
                  <div className="absolute -top-2 -right-2">
                    <Sparkles className="h-6 w-6 text-primary animate-bounce" />
                  </div>
                </div>
                <h3 className="text-xl font-semibold mb-2">No documents yet</h3>
                <p className="text-muted-foreground mb-6 text-center max-w-md">
                  Start by uploading and parsing your first document. We support PDF, DOCX, PPTX, and HTML files.
                </p>
                <Link href="/parse">
                  <Button className="gap-2 transition-all hover:scale-105 hover:shadow-lg">
                    <Upload className="h-4 w-4" />
                    Upload Document
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}

          {/* Documents Grid */}
          {!isLoading && !error && documents.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {documents.map((doc, index) => (
                <Card
                  key={doc.id}
                  className={`
                    group
                    animate-fade-in-up
                    stagger-${Math.min(index + 1, 6)}
                    hover:shadow-xl
                    hover:scale-[1.02]
                    transition-all
                    duration-300
                    cursor-pointer
                    border-2
                    hover:border-primary/50
                    overflow-hidden
                  `}
                >
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-start justify-between gap-2 min-w-0 overflow-hidden">
                      <HoverCard>
                        <HoverCardTrigger asChild>
                          <Tooltip delayDuration={300}>
                            <TooltipTrigger asChild>
                              <span className="truncate flex-1 min-w-0 hover:text-primary transition-colors cursor-pointer block">
                                {doc.document_name}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="max-w-sm">
                              <p className="break-all">{doc.document_name}</p>
                            </TooltipContent>
                          </Tooltip>
                        </HoverCardTrigger>
                        <HoverCardContent className="w-80 max-w-[90vw]" side="top">
                          <div className="space-y-2">
                            <div className="flex items-start gap-2">
                              <FileIcon className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                              <h4 className="text-sm font-semibold break-all flex-1 [overflow-wrap:anywhere]">
                                {doc.document_name}
                              </h4>
                            </div>
                            <div className="text-xs text-muted-foreground space-y-1">
                              <p>Size: {doc.size_kb} KB</p>
                              <p>Parsed: {formatDate(doc.parsed_at)}</p>
                              {doc.table_count > 0 && (
                                <p>Contains {doc.table_count} table{doc.table_count > 1 ? 's' : ''}</p>
                              )}
                            </div>
                            <div className="text-xs bg-muted/50 rounded p-2 max-h-24 overflow-y-auto break-words">
                              {doc.preview}
                            </div>
                          </div>
                        </HoverCardContent>
                      </HoverCard>
                      <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0 group-hover:text-primary transition-colors" />
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2 truncate">
                      <Clock className="h-3 w-3 flex-shrink-0" />
                      <span className="truncate">{formatDate(doc.parsed_at)}</span>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4 pt-0">
                    {/* Preview */}
                    <div className="text-sm text-muted-foreground line-clamp-3 bg-muted/50 rounded p-3 group-hover:bg-muted transition-colors">
                      {doc.preview}
                    </div>

                    {/* Metadata */}
                    <div className="flex gap-2 flex-wrap">
                      {/* Parsing Strategy Badge */}
                      {doc.parsing_metadata && (() => {
                        const { icon: Icon, label, variant } = getParserBadge(doc.parsing_metadata.parser_used);
                        return (
                          <Badge
                            variant={variant}
                            className="gap-1 transition-all group-hover:scale-105"
                          >
                            <Icon className="h-3 w-3" />
                            {label}
                          </Badge>
                        );
                      })()}
                      <Badge variant="secondary" className="gap-1 transition-all group-hover:scale-105">
                        <FileText className="h-3 w-3" />
                        {doc.size_kb} KB
                      </Badge>
                      {doc.table_count > 0 && (
                        <Badge variant="outline" className="gap-1 transition-all group-hover:scale-105 group-hover:border-primary/50">
                          <Table2 className="h-3 w-3" />
                          {doc.table_count} table{doc.table_count > 1 ? 's' : ''}
                        </Badge>
                      )}
                    </div>

                    {/* View Button */}
                    <Link href={`/viewer?file=${doc.document_name}`} className="block">
                      <Button className="w-full gap-2 transition-all group-hover:scale-105 group-hover:shadow-md" variant="outline">
                        View Document
                        <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
    </TooltipProvider>
  );
}
