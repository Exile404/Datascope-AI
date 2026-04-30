"use client";

import { useEffect } from "react";
import { toast } from "sonner";
import { CostConfig } from "@/components/cost/cost-config";
import { ModelComparison } from "@/components/cost/model-comparison";
import { CostTable } from "@/components/cost/cost-table";
import { useProjections } from "@/hooks/use-cost";

export default function CostPage() {
  const { mutate, data, isPending, error } = useProjections();

  useEffect(() => {
    // Run with default values on mount
    mutate({
      daily_calls: 5000,
      avg_input_tokens: 800,
      avg_output_tokens: 400,
    });
  }, [mutate]);

  useEffect(() => {
    if (error) toast.error(error.message);
  }, [error]);

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight">Cost Analyzer</h1>
        <p className="mt-2 text-muted-foreground">
          Project token costs across LLM providers. Compare your self-hosted model
          against industry options.
        </p>
      </div>

      <div className="space-y-6">
        <CostConfig
          onCalculate={(config) => mutate(config)}
          loading={isPending}
        />

        {data && (
          <>
            <ModelComparison projections={data.projections} />
            <CostTable projections={data.projections} />
          </>
        )}

        {!data && isPending && (
          <div className="rounded-2xl border border-border bg-card p-12 text-center text-muted-foreground">
            Calculating costs...
          </div>
        )}
      </div>
    </div>
  );
}