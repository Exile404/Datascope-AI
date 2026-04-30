"use client";

import { Brain, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { HallucinationResponse } from "@/types/drift";

interface HallucinationPanelProps {
  result: HallucinationResponse;
}

export function HallucinationPanel({ result }: HallucinationPanelProps) {
  const ratePct = (result.rate * 100).toFixed(1);

  return (
    <Card className="overflow-hidden">
      <div className={`border-b border-border px-6 py-4 ${
        result.alert ? "bg-red-500/5" : "bg-emerald-500/5"
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-violet-500" />
            <h3 className="text-sm font-semibold uppercase tracking-wider">
              Hallucination Detection
            </h3>
          </div>
          {result.alert ? (
            <Badge className="bg-red-500/10 text-red-500 hover:bg-red-500/10">
              <AlertTriangle className="mr-1 h-3 w-3" />
              Alert
            </Badge>
          ) : (
            <Badge className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/10">
              <CheckCircle2 className="mr-1 h-3 w-3" />
              Clean
            </Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 divide-x divide-border border-b border-border">
        <div className="p-5 text-center">
          <div className={`text-2xl font-bold ${result.alert ? "text-red-500" : "text-emerald-500"}`}>
            {ratePct}%
          </div>
          <div className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">
            Hallucination Rate
          </div>
        </div>
        <div className="p-5 text-center">
          <div className="text-2xl font-bold">{result.flagged_count}</div>
          <div className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">
            Flagged
          </div>
        </div>
        <div className="p-5 text-center">
          <div className="text-2xl font-bold text-muted-foreground">{result.total}</div>
          <div className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">
            Total Checked
          </div>
        </div>
      </div>

      {result.examples.length > 0 && (
        <div className="p-6">
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Flagged Outputs
          </p>
          <div className="space-y-3">
            {result.examples.map((ex, i) => (
              <div
                key={i}
                className="rounded-lg border border-red-500/20 bg-red-500/5 p-3"
              >
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-mono text-xs text-muted-foreground">
                    Output #{ex.index + 1}
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {ex.invented_numbers.map((num, j) => (
                      <Badge
                        key={j}
                        variant="outline"
                        className="border-red-500/40 font-mono text-xs text-red-500"
                      >
                        {num}
                      </Badge>
                    ))}
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">{ex.preview}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}