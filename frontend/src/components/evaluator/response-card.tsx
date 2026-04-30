"use client";

import { Clock, Hash, Thermometer } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { EvaluationResult } from "@/types/evaluator";

interface ResponseCardProps {
  result: EvaluationResult;
  highlight?: boolean;
}

const SCORE_COLORS = {
  excellent: "text-emerald-500",
  good: "text-cyan-500",
  fair: "text-amber-500",
  poor: "text-red-500",
};

function scoreColor(score: number): string {
  if (score >= 90) return SCORE_COLORS.excellent;
  if (score >= 75) return SCORE_COLORS.good;
  if (score >= 60) return SCORE_COLORS.fair;
  return SCORE_COLORS.poor;
}

export function ResponseCard({ result, highlight }: ResponseCardProps) {
  const avgScore = result.scores
    ? (result.scores.relevance + result.scores.coherence + result.scores.completeness + result.scores.factuality) / 4
    : 0;

  return (
    <Card className={`p-5 ${highlight ? "border-violet-500/50 bg-violet-500/5" : ""}`}>
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Thermometer className="h-3.5 w-3.5" />
          <span className="font-mono">temp = {result.temperature.toFixed(1)}</span>
        </div>
        {result.scores && (
          <Badge className={`${scoreColor(avgScore)} bg-transparent border`}>
            {avgScore.toFixed(0)}/100
          </Badge>
        )}
      </div>

      <p className="text-sm leading-relaxed text-foreground">
        {result.answer || result.response}
      </p>

      {result.scores && (
        <div className="mt-4 grid grid-cols-4 gap-2 border-t border-border pt-4">
          {Object.entries(result.scores).map(([key, val]) => (
            <div key={key} className="text-center">
              <div className={`text-lg font-bold ${scoreColor(val)}`}>{val}</div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                {key}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 flex items-center gap-4 border-t border-border pt-3 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <Clock className="h-3 w-3" />
          <span>{(result.latency_ms / 1000).toFixed(2)}s</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Hash className="h-3 w-3" />
          <span>{result.input_tokens}→{result.output_tokens}</span>
        </div>
      </div>
    </Card>
  );
}