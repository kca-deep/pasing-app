'use client';

import { useEffect, useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface Heading {
  level: number;
  text: string;
  id: string;
}

interface TableOfContentsProps {
  content: string;
  className?: string;
}

export function TableOfContents({ content, className }: TableOfContentsProps) {
  const [headings, setHeadings] = useState<Heading[]>([]);
  const [activeId, setActiveId] = useState<string>('');

  useEffect(() => {
    // Extract headings from markdown content
    const extractedHeadings = extractHeadings(content);
    setHeadings(extractedHeadings);

    // Set up intersection observer for active section tracking
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      {
        rootMargin: '-80px 0px -80% 0px',
      }
    );

    // Observe all headings
    extractedHeadings.forEach(({ id }) => {
      const element = document.getElementById(id);
      if (element) {
        observer.observe(element);
      }
    });

    return () => {
      observer.disconnect();
    };
  }, [content]);

  if (headings.length === 0) {
    return null;
  }

  return (
    <nav className={cn('sticky top-20', className)}>
      <h3 className="font-semibold text-sm mb-4">On this page</h3>
      <ScrollArea className="h-[calc(100vh-200px)]">
        <ul className="space-y-2 text-sm">
          {headings.map((heading) => (
            <li
              key={heading.id}
              style={{
                paddingLeft: `${(heading.level - 1) * 0.75}rem`,
              }}
            >
              <a
                href={`#${heading.id}`}
                className={cn(
                  'block py-1 hover:text-foreground transition-colors',
                  activeId === heading.id
                    ? 'text-foreground font-medium'
                    : 'text-muted-foreground'
                )}
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById(heading.id)?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                  });
                }}
              >
                {heading.text}
              </a>
            </li>
          ))}
        </ul>
      </ScrollArea>
    </nav>
  );
}

// Helper function to extract headings from markdown
function extractHeadings(markdown: string): Heading[] {
  const headingRegex = /^(#{1,6})\s+(.+)$/gm;
  const headings: Heading[] = [];
  const seenIds = new Map<string, number>();
  let match;
  let headingIndex = 0;

  while ((match = headingRegex.exec(markdown)) !== null) {
    const level = match[1].length;
    const text = match[2].trim();
    let id = generateId(text);

    // Fallback to index-based ID if generateId returns empty string
    if (!id) {
      id = `heading-${headingIndex}`;
    }

    // Handle duplicate IDs by adding a suffix
    if (seenIds.has(id)) {
      const count = seenIds.get(id)! + 1;
      seenIds.set(id, count);
      id = `${id}-${count}`;
    } else {
      seenIds.set(id, 0);
    }

    headings.push({
      level,
      text,
      id,
    });

    headingIndex++;
  }

  return headings;
}

// Helper function to generate ID from heading text (same as MarkdownViewer)
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

  return id;
}
