'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { CodeBlock } from './CodeBlock';
import { TableReference } from './TableReference';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface MarkdownViewerProps {
  content: string;
  className?: string;
  docName?: string;
}

export function MarkdownViewer({ content, className, docName }: MarkdownViewerProps) {
  // Helper function to check if blockquote contains table reference
  const isTableReference = (children: any): boolean => {
    try {
      const text = String(children);
      // Pattern: "Table XXX" with table reference
      return /Table\s+\d+.*tables\/table_\d+\.json/i.test(text);
    } catch {
      return false;
    }
  };

  // Helper function to extract table ID from blockquote
  const extractTableId = (children: any): string | null => {
    try {
      const text = String(children);
      const match = text.match(/table_(\d+)\.json/i);
      return match ? `table_${match[1]}` : null;
    } catch {
      return null;
    }
  };
  return (
    <div className={cn('prose dark:prose-invert max-w-none overflow-hidden', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // Code blocks with syntax highlighting
          code: CodeBlock,

          // Tables with shadcn/ui styling and horizontal scroll
          table: ({ node, ...props }) => (
            <div className="my-6 w-full">
              <ScrollArea className="w-full rounded-lg border">
                <div className="min-w-full w-max">
                  <Table {...props} />
                </div>
                <ScrollBar orientation="horizontal" />
              </ScrollArea>
            </div>
          ),
          thead: ({ node, ...props }) => <TableHeader {...props} />,
          tbody: ({ node, ...props }) => <TableBody {...props} />,
          tr: ({ node, ...props }) => <TableRow {...props} />,
          th: ({ node, ...props }) => (
            <TableHead className="font-semibold" {...props} />
          ),
          td: ({ node, ...props }) => (
            <TableCell className="max-w-[300px] break-words" {...props} />
          ),

          // Headings with auto-generated IDs for anchor links
          h1: ({ node, children, ...props }) => {
            const id = generateId(String(children));
            return (
              <h1 id={id} className="scroll-mt-20" {...props}>
                <a href={`#${id}`} className="no-underline hover:underline">
                  {children}
                </a>
              </h1>
            );
          },
          h2: ({ node, children, ...props }) => {
            const id = generateId(String(children));
            return (
              <h2 id={id} className="scroll-mt-20" {...props}>
                <a href={`#${id}`} className="no-underline hover:underline">
                  {children}
                </a>
              </h2>
            );
          },
          h3: ({ node, children, ...props }) => {
            const id = generateId(String(children));
            return (
              <h3 id={id} className="scroll-mt-20" {...props}>
                <a href={`#${id}`} className="no-underline hover:underline">
                  {children}
                </a>
              </h3>
            );
          },
          h4: ({ node, children, ...props }) => {
            const id = generateId(String(children));
            return (
              <h4 id={id} className="scroll-mt-20" {...props}>
                <a href={`#${id}`} className="no-underline hover:underline">
                  {children}
                </a>
              </h4>
            );
          },
          h5: ({ node, children, ...props }) => {
            const id = generateId(String(children));
            return (
              <h5 id={id} className="scroll-mt-20" {...props}>
                <a href={`#${id}`} className="no-underline hover:underline">
                  {children}
                </a>
              </h5>
            );
          },
          h6: ({ node, children, ...props }) => {
            const id = generateId(String(children));
            return (
              <h6 id={id} className="scroll-mt-20" {...props}>
                <a href={`#${id}`} className="no-underline hover:underline">
                  {children}
                </a>
              </h6>
            );
          },

          // External links open in new tab
          a: ({ node, href, children, ...props }) => {
            const isExternal = href?.startsWith('http');
            return (
              <a
                href={href}
                target={isExternal ? '_blank' : undefined}
                rel={isExternal ? 'noopener noreferrer' : undefined}
                {...props}
              >
                {children}
              </a>
            );
          },

          // Blockquote with table reference detection
          blockquote: ({ node, children, ...props }) => {
            if (docName && isTableReference(children)) {
              const tableId = extractTableId(children);
              if (tableId) {
                return <TableReference tableId={tableId} docName={docName} />;
              }
            }
            return (
              <blockquote
                className="border-l-4 border-border pl-4 italic text-muted-foreground"
                {...props}
              >
                {children}
              </blockquote>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

// Helper function to generate ID from heading text
function generateId(text: string): string {
  // First try standard slug generation
  let id = text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-')
    .replace(/^-+/, '')
    .replace(/-+$/, '');

  // If empty (e.g., text was all special chars or non-ASCII),
  // encode the original text to create a valid ID
  if (!id) {
    id = encodeURIComponent(text.toLowerCase().trim()).replace(/%/g, '-');
  }

  // Final fallback if still empty
  if (!id) {
    id = `heading-${Math.random().toString(36).substr(2, 9)}`;
  }

  return id;
}
