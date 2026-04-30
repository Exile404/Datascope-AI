"use client";

import { useEffect, useState } from "react";
import { Loader2, AlertCircle, History } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PromptInput } from "@/components/evaluator/prompt-input";
import { ResponseCard } from "@/components/evaluator/response-card";
import { ScoreRadar } from "@/components/evaluator/score-radar";
import { useEvaluate, useCompare, useEvalHistory } from "@/hooks/use-evaluator";
import type { EvaluationResult } from "@/types/evaluator";

export default function EvaluatorPage() {
  const evalMutation = useEvaluate();
  const compareMutation = useCompare();
  const { data: historyData } = useEvalHistory(10);

  const [results, setResults] = useState<EvaluationResult[]>([]);

  const isPending = evalMutation.isPending || compareMutation.isPending;
  const error = evalMutation.error || compareMutation.error;

  useEffect(() => {
    if (error) toast.error(error.message);
  }, [error]);

  const handleSubmit = async (
    mode: "single" | "compare",
    payload: {
      prompt: string;
      system: string;
      temperature?: number;
      temperatures?: number[];
    }
  ) => {
    setResults([]);

    if (mode === "single") {
      evalMutation.mutate(
        {
          prompt: payload.prompt,
          system: payload.system,
          temperature: payload.temperature,
        },
        {
          onSuccess: (data) => setResults([data]),
        }
      );
    } else {
      compareMutation.mutate(
        {
          prompt: payload.prompt,
          system: payload.system,
          temperatures: payload.temperatures,
        },
        {
          onSuccess: (data) => setResults(data.results),
        }
      );
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight">LLM Evaluator</h1>
        <p className="mt-2 text-muted-foreground">
          Test prompts and compare model outputs across temperature settings with
          automated quality scoring (relevance, coherence, completeness, factuality).
        </p>
      </div>

      <div className="space-y-6">
        <PromptInput onSubmit={handleSubmit} loading={isPending} />

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        )}

        {isPending && (
          <Card className="p-12 text-center">
            <Loader2 className="mx-auto h-10 w-10 animate-spin text-violet-500" />
            <p className="mt-4 text-base font-medium">Running evaluation...</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {compareMutation.isPending
                ? "Running 3 inferences in parallel + scoring each. ~30-90 seconds."
                : "Generating response and scoring quality. ~10-30 seconds."}
            </p>
          </Card>
        )}

        {results.length > 0 && (
          <>
            {results.length > 1 && <ScoreRadar results={results} />}

            <div className={`grid gap-4 ${results.length === 3 ? "md:grid-cols-3" : ""}`}>
              {results.map((r, i) => (
                <ResponseCard key={i} result={r} highlight={results.length === 1} />
              ))}
            </div>
          </>
        )}

        {historyData && historyData.records.length > 0 && (
          <Card className="overflow-hidden">
            <div className="border-b border-border px-6 py-4">
              <div className="flex items-center gap-2">
                <History className="h-4 w-4 text-violet-500" />
                <h3 className="text-sm font-semibold uppercase tracking-wider">
                  Recent Evaluations
                </h3>
              </div>
            </div>
            <div className="divide-y divide-border">
              {historyData.records.slice(0, 5).map((record) => {
                const avgScore = record.scores
                  ? (record.scores.relevance + record.scores.coherence + record.scores.completeness + record.scores.factuality) / 4
                  : null;
                return (
                  <div key={record.id} className="px-6 py-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm">{record.prompt}</p>
                        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                          <span>{new Date(record.timestamp).toLocaleString()}</span>
                          <span>·</span>
                          <span className="font-mono">temp {record.temperature.toFixed(1)}</span>
                          <span>·</span>
                          <span>{(record.latency_ms / 1000).toFixed(1)}s</span>
                        </div>
                      </div>
                      {avgScore !== null && (
                        <div className="text-right">
                          <div className="text-sm font-bold text-emerald-500">
                            {avgScore.toFixed(0)}
                          </div>
                          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                            score
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}