
"use client";

import { useEffect } from "react";
import { Loader2, RotateCcw, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CSVDropzone } from "@/components/profiler/csv-dropzone";
import { StatsCards } from "@/components/profiler/stats-cards";
import { InsightPanel } from "@/components/profiler/insight-panel";
import { useInsight } from "@/hooks/use-profiler";

export default function ProfilerPage() {
  const { mutate, data, isPending, error, reset } = useInsight();

  useEffect(() => {
    if (error) toast.error(error.message);
  }, [error]);

  const handleFileSelect = (file: File) => {
    mutate({ file, datasetName: file.name });
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight">Data Profiler</h1>
        <p className="mt-2 text-muted-foreground">
          Upload a CSV to get automated EDA, statistical analysis, and AI-powered insights.
        </p>
      </div>

      {!data && !isPending && (
        <CSVDropzone onFileSelect={handleFileSelect} disabled={isPending} />
      )}

      {isPending && (
        <div className="rounded-2xl border border-border bg-card p-12 text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-violet-500" />
          <p className="mt-4 text-base font-medium">Analyzing your data...</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Profiling statistics and generating AI insights. This can take 30-90 seconds.
          </p>
        </div>
      )}

      {error && !isPending && (
        <Alert variant="destructive" className="mt-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error.message}
            <Button
              variant="ghost"
              size="sm"
              onClick={reset}
              className="ml-2 h-7 text-xs"
            >
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {data && !isPending && (
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">{data.dataset_name}</h2>
              <p className="text-sm text-muted-foreground">
                {data.profile.num_rows.toLocaleString()} rows ·{" "}
                {data.profile.num_columns} columns
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={reset}>
              <RotateCcw className="mr-2 h-3.5 w-3.5" />
              Analyze another file
            </Button>
          </div>

          <StatsCards profile={data.profile} />

          <InsightPanel thinking={data.thinking} answer={data.answer} />
        </div>
      )}
    </div>
  );
}