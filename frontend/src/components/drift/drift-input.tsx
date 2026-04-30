"use client";

import { useState } from "react";
import { Activity, Brain } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

type Mode = "drift" | "hallucination";

interface DriftInputProps {
  onDetectDrift: (baseline: string[], current: string[]) => void;
  onCheckHallucinations: (outputs: string[], context: string) => void;
  loading?: boolean;
}

const SAMPLE_BASELINE = `The dataset shows a normal distribution
Quality score is excellent at 95%
No significant outliers detected`;

const SAMPLE_CURRENT = `The data appears highly skewed
Quality has degraded significantly
Many outliers found in income column`;

const SAMPLE_OUTPUTS = `Mean is 35.4 with std 11.1
Strong correlation r=0.85 between age and income
Mean salary is 75000 dollars`;

const SAMPLE_CONTEXT = `Dataset has 2000 rows. Age column mean=35.4, std=11.1`;

function splitLines(text: string): string[] {
  return text
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function DriftInput({ onDetectDrift, onCheckHallucinations, loading }: DriftInputProps) {
  const [mode, setMode] = useState<Mode>("drift");
  const [baseline, setBaseline] = useState(SAMPLE_BASELINE);
  const [current, setCurrent] = useState(SAMPLE_CURRENT);
  const [outputs, setOutputs] = useState(SAMPLE_OUTPUTS);
  const [context, setContext] = useState(SAMPLE_CONTEXT);

  const handleSubmit = () => {
    if (mode === "drift") {
      onDetectDrift(splitLines(baseline), splitLines(current));
    } else {
      onCheckHallucinations(splitLines(outputs), context);
    }
  };

  return (
    <Card className="p-6">
      <div className="mb-4 flex gap-1 rounded-lg bg-muted/50 p-1">
        <button
          onClick={() => setMode("drift")}
          className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            mode === "drift"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Activity className="mr-1.5 inline h-3 w-3" />
          Detect Drift
        </button>
        <button
          onClick={() => setMode("hallucination")}
          className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            mode === "hallucination"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Brain className="mr-1.5 inline h-3 w-3" />
          Check Hallucinations
        </button>
      </div>

      {mode === "drift" ? (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="baseline">Baseline Outputs</Label>
              <Textarea
                id="baseline"
                value={baseline}
                onChange={(e) => setBaseline(e.target.value)}
                rows={5}
                placeholder="One output per line"
              />
              <p className="text-xs text-muted-foreground">
                {splitLines(baseline).length} samples
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="current">Current Outputs</Label>
              <Textarea
                id="current"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
                rows={5}
                placeholder="One output per line"
              />
              <p className="text-xs text-muted-foreground">
                {splitLines(current).length} samples
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="context">Source Context</Label>
            <Textarea
              id="context"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={3}
              placeholder="Original data the model should reference"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="outputs">Model Outputs to Check</Label>
            <Textarea
              id="outputs"
              value={outputs}
              onChange={(e) => setOutputs(e.target.value)}
              rows={5}
              placeholder="One output per line"
            />
            <p className="text-xs text-muted-foreground">
              {splitLines(outputs).length} outputs · numbers not in context will be flagged
            </p>
          </div>
        </div>
      )}

      <Button onClick={handleSubmit} disabled={loading} className="mt-4 w-full md:w-auto">
        {loading ? "Analyzing..." : mode === "drift" ? "Detect Drift" : "Check Hallucinations"}
      </Button>
    </Card>
  );
}