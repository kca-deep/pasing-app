'use client';

import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Button } from '@/components/ui/button';
import { Check, Copy } from 'lucide-react';

interface CodeBlockProps {
  children?: React.ReactNode;
  className?: string;
  node?: any;
  inline?: boolean;
}

export function CodeBlock({ children, className, inline, ...rest }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const codeString = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    await navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Inline code
  if (inline || !match) {
    return (
      <code
        className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold break-words"
        {...rest}
      >
        {children}
      </code>
    );
  }

  // Code block with syntax highlighting
  return (
    <div className="relative group my-4 overflow-hidden rounded-lg">
      <div className="absolute right-2 top-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          size="sm"
          variant="ghost"
          className="h-8 px-2 bg-background/80 backdrop-blur-sm"
          onClick={handleCopy}
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 mr-1" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="h-4 w-4 mr-1" />
              Copy
            </>
          )}
        </Button>
      </div>
      <SyntaxHighlighter
        {...rest}
        PreTag="div"
        language={language}
        style={vscDarkPlus}
        showLineNumbers={true}
        wrapLongLines={false}
        customStyle={{
          margin: 0,
          borderRadius: '0.5rem',
          padding: '1rem',
          maxWidth: '100%',
          overflowX: 'auto',
        }}
      >
        {codeString}
      </SyntaxHighlighter>
    </div>
  );
}
