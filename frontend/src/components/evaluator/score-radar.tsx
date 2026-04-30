"use client";

import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Legend
} from "recharts";
import { Card } from "@/components/ui/card";
import { Brain } from "lucide-react";
import type { EvaluationResult } from "@/types/evaluator";

interface ScoreRadarProps {
  results: EvaluationResult[];
}

const COLORS = ["#6c5ce7", "#06b6d4", "#f59e0b"];

export function ScoreRadar({ results }: ScoreRadarProps) {
  const dimensions = ["relevance", "coherence", "completeness", "factuality"] as const;

  const data = dimensions.map((dim) => {
    const point: Record<string, string | number> = {
      dimension: dim.charAt(0).toUpperCase() + dim.slice(1),
    };
    results.forEach((r, i) => {
      point[`temp_${r.temperature.toFixed(1)}`] = r.scores?.[dim] ?? 0;
    });
    return point;
  });

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center gap-2">
        <Brain className="h-4 w-4 text-violet-500" />
        <h3 className="text-sm font-semibold uppercase tracking-wider">
          Quality Comparison
        </h3>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <RadarChart data={data}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: "hsl(var(--foreground))", fontSize: 12 }}
          />
          <PolarRadiusAxis
            domain={[0, 100]}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
          />
          {results.map((r, i) => (
            <Radar
              key={i}
              name={`temp ${r.temperature.toFixed(1)}`}
              dataKey={`temp_${r.temperature.toFixed(1)}`}
              stroke={COLORS[i % COLORS.length]}
              fill={COLORS[i % COLORS.length]}
              fillOpacity={0.15}
              strokeWidth={2}
            />
          ))}
          <Legend wrapperStyle={{ fontSize: 11 }} />
        </RadarChart>
      </ResponsiveContainer>
    </Card>
  );
}