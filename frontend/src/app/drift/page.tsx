"use client";

import { useEffect, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { DriftInput } from "@/components/drift/drift-input";
import { DriftKPICards } from "@/components/drift/drift-kpi-cards";
import { AlertFeed } from "@/components/drift/alert-feed";
import { DriftChart } from "@/components/drift/drift-chart";
import { HallucinationPanel } from "@/components/drift/hallucination-panel";
import { useDetectDrift, useFlagHallucinations } from "@/hooks/use-drift";
import type { DriftResponse, HallucinationResponse } from "@/types/drift";

export default function DriftPage() {
  const driftMutation = useDetectDrift();
  const halluMutation = useFlagHallucinations();

  const [driftResult, setDriftResult] = useState<DriftResponse | null>(null);
  const [halluResult, setHalluResult] = useState<HallucinationResponse | null>(null);

  const isPending = driftMutation.isPending || halluMutation.isPending;
  const error = driftMutation.error || halluMutation.error;

  useEffect(() => {
    if (error) toast.error(error.message);
  }, [error]);

  const handleDrift = (baseline: string[], current: string[]) => {
    setHalluResult(null);
    driftMutation.mutate(
      { baseline_outputs: baseline, current_outputs: current },
      { onSuccess: (data) => setDriftResult(data) }
    );
  };

  const handleHallucinations = (outputs: string[], context: string) => {
    setDriftResult(null);
    halluMutation.mutate(
      { outputs, source_context: context },
      { onSuccess: (data) => setHalluResult(data) }
    );
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight">Drift Monitor</h1>
        <p className="mt-2 text-muted-foreground">
          Track LLM output drift over time, detect hallucinated content, and monitor
          performance degradation across deployments.
        </p>
      </div>

      <div className="space-y-6">
        <DriftInput
          onDetectDrift={handleDrift}
          onCheckHallucinations={handleHallucinations}
          loading={isPending}
        />

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        )}

        {isPending && (
          <Card className="p-12 text-center">
            <Loader2 className="mx-auto h-10 w-10 animate-spin text-violet-500" />
            <p className="mt-4 text-base font-medium">
              {driftMutation.isPending ? "Computing drift..." : "Checking hallucinations..."}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {driftMutation.isPending
                ? "Computing embeddings and statistical drift (first run downloads model ~80MB)"
                : "Scanning outputs for invented numbers and entities"}
            </p>
          </Card>
        )}

        {driftResult && !isPending && (
          <>
            <DriftKPICards
              semantic={driftResult.semantic}
              outputStats={driftResult.output_stats}
            />
            <AlertFeed alerts={driftResult.alerts} />
          </>
        )}

        {halluResult && !isPending && <HallucinationPanel result={halluResult} />}

        <div className="grid gap-4 md:grid-cols-2">
          <DriftChart
            metric="centroid_drift"
            title="Centroid Drift History"
            threshold={0.3}
            color="#6c5ce7"
          />
          <DriftChart
            metric="hallucination_rate"
            title="Hallucination Rate"
            threshold={0.05}
            color="#ef4444"
          />
        </div>
      </div>
    </div>
  );
}