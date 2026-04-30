"use client";

import { useState } from "react";
import { Calculator } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ProjectionRequest } from "@/types/cost";

interface CostConfigProps {
  onCalculate: (config: ProjectionRequest) => void;
  loading?: boolean;
}

export function CostConfig({ onCalculate, loading }: CostConfigProps) {
  const [config, setConfig] = useState<ProjectionRequest>({
    daily_calls: 5000,
    avg_input_tokens: 800,
    avg_output_tokens: 400,
  });

  const update = (field: keyof ProjectionRequest, value: number) => {
    setConfig((c) => ({ ...c, [field]: value }));
  };

  return (
    <Card className="p-6">
      <div className="mb-6 flex items-center gap-2">
        <Calculator className="h-4 w-4 text-violet-500" />
        <h3 className="text-sm font-semibold uppercase tracking-wider">Configuration</h3>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor="daily_calls">Daily Calls</Label>
          <Input
            id="daily_calls"
            type="number"
            min={1}
            value={config.daily_calls}
            onChange={(e) => update("daily_calls", Number(e.target.value))}
          />
          <p className="text-xs text-muted-foreground">
            Expected requests per day
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="avg_input">Avg Input Tokens</Label>
          <Input
            id="avg_input"
            type="number"
            min={1}
            value={config.avg_input_tokens}
            onChange={(e) => update("avg_input_tokens", Number(e.target.value))}
          />
          <p className="text-xs text-muted-foreground">
            Tokens per prompt
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="avg_output">Avg Output Tokens</Label>
          <Input
            id="avg_output"
            type="number"
            min={1}
            value={config.avg_output_tokens}
            onChange={(e) => update("avg_output_tokens", Number(e.target.value))}
          />
          <p className="text-xs text-muted-foreground">
            Tokens per response
          </p>
        </div>
      </div>

      <Button
        onClick={() => onCalculate(config)}
        disabled={loading}
        className="mt-6 w-full md:w-auto"
      >
        {loading ? "Calculating..." : "Calculate Costs"}
      </Button>
    </Card>
  );
}