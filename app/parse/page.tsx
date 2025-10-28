'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileUploader } from '@/components/upload/FileUploader';
import { ParsingOptions } from '@/components/upload/ParsingOptions';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { uploadFile, parseDocumentAsync, getParsingStatus } from '@/lib/api';
import type { ParseOptions } from '@/lib/types';
import { AlertCircle, AlertTriangle, FileText, Sparkles, Zap } from 'lucide-react';

export default function ParsePage() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [options, setOptions] = useState<ParseOptions>({
    // Default strategy: Camelot + Docling (Hybrid, High-Accuracy Table Extraction)
    use_dolphin: false,
    use_mineru: false,
    use_camelot: true,

    // Camelot options
    camelot_mode: 'hybrid',

    // Common options
    output_format: 'markdown',
    extract_tables: true,
    save_to_output_folder: true,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');

  const handleParse = async () => {
    if (!selectedFile) {
      setError('Please select a file to parse');
      return;
    }

    setIsLoading(true);
    setError(null);
    setWarnings([]);
    setProgress(0);

    try {
      // Step 1: Upload file to backend
      setProgressMessage('Uploading file...');
      setProgress(10);

      await uploadFile(selectedFile);

      // Step 2: Start async parsing job
      setProgressMessage('Starting parsing job...');
      setProgress(20);

      const jobResponse = await parseDocumentAsync({
        filename: selectedFile.name,
        options,
      });

      // Step 3: Poll for job status
      const jobId = jobResponse.job_id;
      let pollingInterval: NodeJS.Timeout | null = null;

      const pollStatus = async () => {
        try {
          const status = await getParsingStatus(jobId);

          // Update progress
          setProgress(Math.max(20, status.progress));
          setProgressMessage(status.message || 'Processing...');

          if (status.status === 'completed') {
            // Clear polling
            if (pollingInterval) clearInterval(pollingInterval);

            const result = status.result;
            if (result) {
              // Check for warnings
              if (result.warnings && result.warnings.length > 0) {
                setWarnings(result.warnings);
              }

              setProgressMessage('Parsing complete!');
              setProgress(100);

              // Wait a bit to show success message
              await new Promise(resolve => setTimeout(resolve, result.warnings ? 2000 : 500));

              // Navigate to viewer with filename
              router.push(`/viewer?file=${encodeURIComponent(selectedFile.name)}`);
            }

            setIsLoading(false);
          } else if (status.status === 'failed') {
            // Clear polling
            if (pollingInterval) clearInterval(pollingInterval);

            setError(status.error || 'Parsing failed. Please try again.');
            setProgress(0);
            setIsLoading(false);
          }
        } catch (err) {
          // Error polling status
          if (pollingInterval) clearInterval(pollingInterval);
          setError(err instanceof Error ? err.message : 'Failed to get parsing status');
          setProgress(0);
          setIsLoading(false);
        }
      };

      // Start polling every 2 seconds
      pollingInterval = setInterval(pollStatus, 2000);

      // Initial poll
      await pollStatus();

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Parsing failed. Please try again.');
      setProgress(0);
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Hero Section */}
        <div className="mb-8 animate-fade-in-up">
          <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
            Document Parser
            <Sparkles className="h-8 w-8 text-primary animate-pulse" />
          </h1>
          <p className="text-muted-foreground flex items-center gap-2">
            <Zap className="h-4 w-4 text-accent" />
            Upload and parse your documents with advanced table extraction
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: File Upload */}
          <div className="space-y-6 animate-fade-in-up stagger-1">
            <FileUploader
              onFileSelect={setSelectedFile}
              selectedFile={selectedFile}
              onFileRemove={() => setSelectedFile(null)}
            />

            {/* Parse Button */}
            <Button
              className="w-full transition-all hover:scale-[1.02] hover:shadow-lg"
              size="lg"
              onClick={handleParse}
              disabled={!selectedFile || isLoading}
            >
              <FileText className="mr-2 h-5 w-5" />
              {isLoading ? 'Parsing...' : 'Parse Document'}
            </Button>

            {/* Progress */}
            {isLoading && (
              <div className="space-y-2 animate-fade-in">
                <Progress value={progress} className="w-full" />
                <p className="text-sm text-center text-muted-foreground animate-pulse">
                  {progressMessage}
                </p>
              </div>
            )}

            {/* Warning Messages */}
            {warnings.length > 0 && (
              <Alert variant="default" className="animate-scale-in border-amber-500/50 bg-amber-500/10">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <AlertDescription>
                  <div className="space-y-1">
                    {warnings.map((warning, idx) => (
                      <p key={idx} className="text-sm text-amber-800 dark:text-amber-200">
                        {warning}
                      </p>
                    ))}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Error Message */}
            {error && (
              <Alert variant="destructive" className="animate-scale-in">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <div className="whitespace-pre-wrap font-mono text-sm">
                    {error}
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Right Column: Parsing Options */}
          <div className="animate-fade-in-up stagger-2">
            <ParsingOptions options={options} onOptionsChange={setOptions} />
          </div>
        </div>
      </div>
    </div>
  );
}
