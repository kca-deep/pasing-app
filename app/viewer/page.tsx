'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, AlertCircle, FileText } from 'lucide-react';
import Link from 'next/link';
import { getParseResult } from '@/lib/api';
import type { ParseResponse } from '@/lib/types';
import { MarkdownViewer } from '@/components/viewer/MarkdownViewer';
import { TableOfContents } from '@/components/viewer/TableOfContents';
import { MetadataPanel } from '@/components/viewer/MetadataPanel';
import { MobileTOC } from '@/components/viewer/MobileTOC';

function ViewerContent() {
  const searchParams = useSearchParams();
  const filename = searchParams.get('file');
  const [result, setResult] = useState<ParseResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const loadResult = async () => {
      if (!filename) {
        setError('No file specified');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const data = await getParseResult(filename);
        if (data.success) {
          setResult(data);
        } else {
          setError(data.error || 'Failed to load result');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load document');
      } finally {
        setIsLoading(false);
      }
    };

    loadResult();
  }, [filename]);

  // Scroll detection for header shadow
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  if (isLoading) {
    return <ViewerSkeleton />;
  }

  if (error || !result) {
    return (
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          {/* Sticky Header */}
          <div className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 border-b border-border/40 -mx-4 px-4 py-4 mb-6">
            <div className="flex items-center gap-3">
              <Link href="/">
                <Button variant="ghost" size="sm" className="transition-all hover:scale-105">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>
              </Link>
              <div className="h-4 w-px bg-border" />
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-sm font-medium text-foreground truncate">
                  {filename || 'Document'}
                </span>
              </div>
            </div>
          </div>
          <Alert variant="destructive" className="animate-scale-in">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error || 'Failed to load document'}</AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4">
      <div className="max-w-[1600px] mx-auto">
        {/* Sticky Header */}
        <div className={`
          sticky top-0 z-50
          bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80
          border-b border-border/40
          -mx-4 px-4 py-4 mb-6
          animate-fade-in
          transition-shadow duration-300
          ${isScrolled ? 'shadow-md' : ''}
        `}>
          <div className="flex items-center gap-3">
            <Link href="/">
              <Button variant="ghost" size="sm" className="transition-all hover:scale-105">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
            </Link>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <span className="text-sm font-medium text-foreground truncate">
                {filename}
              </span>
            </div>
          </div>
        </div>

        {/* 3-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[250px_1fr] xl:grid-cols-[250px_1fr_300px] gap-6">
          {/* Left: Table of Contents (hidden on mobile, sticky) */}
          <aside className="hidden lg:block">
            <div className="sticky top-24 max-h-[calc(100vh-7rem)] overflow-y-auto">
              {result.markdown && (
                <TableOfContents content={result.markdown} />
              )}
            </div>
          </aside>

          {/* Center: Markdown Content */}
          <main className="min-w-0">
            <Card className="p-8 overflow-hidden animate-fade-in-up">
              {result.markdown ? (
                <MarkdownViewer
                  content={result.markdown}
                  docName={filename ? filename.replace(/\.[^.]+$/, '') : undefined}
                />
              ) : (
                <div className="text-center text-muted-foreground py-12">
                  <p>No content available</p>
                </div>
              )}
            </Card>
          </main>

          {/* Right: Metadata Panel (hidden on tablet and below, sticky) */}
          <aside className="hidden xl:block">
            <div className="sticky top-24 max-h-[calc(100vh-7rem)] overflow-y-auto">
              <MetadataPanel result={result} filename={filename || ''} />
            </div>
          </aside>
        </div>

        {/* Mobile Metadata (visible only on tablet and below) */}
        <div className="xl:hidden mt-6 animate-fade-in-up stagger-2">
          <MetadataPanel result={result} filename={filename || ''} />
        </div>

        {/* Mobile TOC Floating Button */}
        {result.markdown && <MobileTOC content={result.markdown} />}
      </div>
    </div>
  );
}

function ViewerSkeleton() {
  return (
    <div className="container mx-auto px-4">
      <div className="max-w-[1600px] mx-auto">
        {/* Sticky Header Skeleton */}
        <div className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 border-b border-border/40 -mx-4 px-4 py-4 mb-6 animate-fade-in">
          <div className="flex items-center gap-3">
            <Skeleton className="h-9 w-20" />
            <Skeleton className="h-4 w-px" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>

        {/* 3-Column Layout Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-[250px_1fr] xl:grid-cols-[250px_1fr_300px] gap-6">
          {/* TOC Skeleton (sticky) */}
          <aside className="hidden lg:block">
            <div className="sticky top-24 space-y-2 animate-scale-in">
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          </aside>

          {/* Content Skeleton */}
          <main className="min-w-0">
            <Card className="p-8 animate-fade-in-up stagger-1">
              <div className="space-y-4">
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-32 w-full mt-8" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
              </div>
            </Card>
          </main>

          {/* Metadata Skeleton (sticky) */}
          <aside className="hidden xl:block">
            <div className="sticky top-24 animate-scale-in stagger-2">
              <Card className="p-6">
                <Skeleton className="h-6 w-32 mb-4" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-5/6" />
                </div>
              </Card>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default function ViewerPage() {
  return (
    <Suspense fallback={<ViewerSkeleton />}>
      <ViewerContent />
    </Suspense>
  );
}
