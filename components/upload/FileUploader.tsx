'use client';

import { useState, useRef } from 'react';
import { Upload, File as FileIcon, X } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onFileRemove: () => void;
}

export function FileUploader({ onFileSelect, selectedFile, onFileRemove }: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFile = (file: File) => {
    // Validate file extension
    const validExtensions = ['.pdf', '.docx', '.pptx', '.html'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!validExtensions.includes(fileExtension)) {
      alert(`Invalid file type. Please select a PDF, DOCX, PPTX, or HTML file.`);
      return;
    }

    // Validate file size (max 50MB)
    const maxSizeInBytes = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSizeInBytes) {
      alert(`File size exceeds 50MB. Please select a smaller file.`);
      return;
    }

    onFileSelect(file);
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <Card className="p-6 transition-all hover:shadow-lg">
      <div
        className={`
          border-2 border-dashed rounded-lg p-12 text-center
          transition-all duration-300 cursor-pointer
          ${isDragging
            ? 'border-primary bg-primary/10 scale-[1.02]'
            : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50'
          }
        `}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => !selectedFile && handleButtonClick()}
      >
        {selectedFile ? (
          <div className="flex items-center justify-between animate-scale-in">
            <div className="flex items-center gap-3">
              <FileIcon className="h-8 w-8 text-primary animate-pulse" />
              <div className="text-left">
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => {
                e.stopPropagation();
                onFileRemove();
              }}
              className="transition-all hover:scale-110 hover:bg-destructive/10"
            >
              <X className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <Upload className={`h-12 w-12 mx-auto text-muted-foreground transition-all ${
              isDragging ? 'scale-110 text-primary animate-bounce' : 'group-hover:scale-105'
            }`} />
            <div>
              <p className="text-lg font-medium">Drag and drop your file here</p>
              <p className="text-sm text-muted-foreground mt-1">
                or click to browse
              </p>
            </div>
            <Button
              onClick={(e) => {
                e.stopPropagation();
                handleButtonClick();
              }}
              variant="secondary"
              className="transition-all hover:scale-105 hover:shadow-md"
            >
              Select File
            </Button>
            <p className="text-xs text-muted-foreground">
              Supported formats: PDF, DOCX, PPTX, HTML (Max 50MB)
            </p>
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.pptx,.html"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      </div>
    </Card>
  );
}
