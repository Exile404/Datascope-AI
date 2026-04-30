"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from "recharts";
import { Card } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";
import { useDriftHistory } from "@/hooks/use-drift";

interface DriftChartProps {
  metric: string;
  title: string;
  threshold?: number;
  color?: string;
}

export function DriftChart({ metric, title, threshold, color = "#6c5ce7" }: DriftChartProps) {
  const { data, isLoading } = useDriftHistory(metric, 30);

  const chartData = data?.points.map((p) => ({
    time: new Date(p.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    value: p.value,
  })) ?? [];

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4" style={{ color }} />
          <h3 className="text-sm font-semibold uppercase tracking-wider">{title}</h3>
        </div>
        <span className="font-mono text-xs text-muted-foreground">
          {chartData.length} data points
        </span>
      </div>

      {isLoading ? (
        <div className="flex h-[220px] items-center justify-center text-sm text-muted-foreground">
          Loading...
        </div>
      ) : chartData.length === 0 ? (
        <div className="flex h-[220px] items-center justify-center text-sm text-muted-foreground">
          No data yet — run drift detection to populate
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
            <XAxis
              dataKey="time"
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                background: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            {threshold !== undefined && (
              <ReferenceLine
                y={threshold}
                stroke="#ef4444"
                strokeDasharray="3 3"
                label={{ value: "threshold", fill: "#ef4444", fontSize: 10 }}
              />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}