"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileSpreadsheet, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ACCEPTED_FILE_TYPES, MAX_UPLOAD_SIZE_MB } from "@/lib/constants";

interface CSVDropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function CSVDropzone({ onFileSelect, disabled }: CSVDropzoneProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setError(null);
      const file = acceptedFiles[0];
      if (!file) return;

      const sizeMB = file.size / 1024 / 1024;
      if (sizeMB > MAX_UPLOAD_SIZE_MB) {
        setError(`File too large (${sizeMB.toFixed(1)} MB). Max: ${MAX_UPLOAD_SIZE_MB} MB`);
        return;
      }

      setSelectedFile(file);
    },
    []
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxFiles: 1,
    disabled: disabled || !!selectedFile,
  });

  const handleAnalyze = () => {
    if (selectedFile) onFileSelect(selectedFile);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setError(null);
  };

  if (selectedFile) {
    return (
      <div className="rounded-2xl border border-border bg-card p-8">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-violet-500/10">
            <FileSpreadsheet className="h-6 w-6 text-violet-500" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate font-medium">{selectedFile.name}</p>
            <p className="text-sm text-muted-foreground">
              {(selectedFile.size / 1024).toFixed(1)} KB
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={handleClear} disabled={disabled}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="mt-6 flex gap-2">
          <Button onClick={handleAnalyze} disabled={disabled} className="flex-1">
            {disabled ? "Analyzing..." : "Analyze with AI"}
          </Button>
          <Button variant="outline" onClick={handleClear} disabled={disabled}>
            Choose Different File
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div
        {...getRootProps()}
        className={cn(
          "rounded-2xl border-2 border-dashed p-12 text-center transition-colors cursor-pointer",
          isDragActive && !isDragReject && "border-violet-500 bg-violet-500/5",
          isDragReject && "border-red-500 bg-red-500/5",
          !isDragActive && "border-border hover:border-foreground/30 hover:bg-muted/30",
          disabled && "pointer-events-none opacity-50"
        )}
      >
        <input {...getInputProps()} />
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-muted">
          <Upload className="h-7 w-7 text-muted-foreground" />
        </div>
        <p className="mt-4 text-base font-medium">
          {isDragActive ? "Drop your CSV here" : "Drag & drop a CSV file"}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          or click to browse · max {MAX_UPLOAD_SIZE_MB} MB
        </p>
      </div>

      {error && (
        <p className="mt-3 text-center text-sm text-red-500">{error}</p>
      )}
    </div>
  );
}