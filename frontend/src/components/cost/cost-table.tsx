"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trophy } from "lucide-react";
import type { ModelProjection } from "@/types/cost";

interface CostTableProps {
  projections: ModelProjection[];
}

export function CostTable({ projections }: CostTableProps) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-border px-6 py-4">
        <div className="flex items-center gap-2">
          <Trophy className="h-4 w-4 text-violet-500" />
          <h3 className="text-sm font-semibold uppercase tracking-wider">
            Cost Breakdown
          </h3>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Rank
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Model
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Daily
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Monthly
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Annual
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Pricing (per 1M)
              </th>
            </tr>
          </thead>
          <tbody>
            {projections.map((p, idx) => {
              const isYourModel = p.model === "datascope-analyst";
              return (
                <tr
                  key={p.model}
                  className={`border-b border-border last:border-0 ${
                    isYourModel ? "bg-emerald-500/5" : ""
                  }`}
                >
                  <td className="px-6 py-3 font-mono text-xs text-muted-foreground">
                    #{idx + 1}
                  </td>
                  <td className="px-6 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{p.model}</span>
                      {isYourModel && (
                        <Badge className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/10">
                          Yours
                        </Badge>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-3 text-right font-mono text-xs">
                    ${p.daily_cost.toFixed(2)}
                  </td>
                  <td className="px-6 py-3 text-right font-mono text-xs font-semibold">
                    ${p.monthly_cost.toLocaleString()}
                  </td>
                  <td className="px-6 py-3 text-right font-mono text-xs">
                    ${p.annual_cost.toLocaleString()}
                  </td>
                  <td className="px-6 py-3 text-right font-mono text-xs text-muted-foreground">
                    ${p.input_pricing_per_1m} / ${p.output_pricing_per_1m}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}