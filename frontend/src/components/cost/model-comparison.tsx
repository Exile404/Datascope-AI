"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid
} from "recharts";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp } from "lucide-react";
import type { ModelProjection } from "@/types/cost";

interface ModelComparisonProps {
  projections: ModelProjection[];
}

const COLORS = {
  free: "#10b981",
  cheap: "#06b6d4",
  mid: "#f59e0b",
  expensive: "#ef4444",
};

function getColor(monthlyCost: number): string {
  if (monthlyCost === 0) return COLORS.free;
  if (monthlyCost < 100) return COLORS.cheap;
  if (monthlyCost < 1000) return COLORS.mid;
  return COLORS.expensive;
}

export function ModelComparison({ projections }: ModelComparisonProps) {
  const cheapest = projections.find((p) => p.monthly_cost > 0);
  const yourModel = projections.find((p) => p.model === "datascope-analyst");

  const chartData = projections.map((p) => ({
    name: p.model.replace(/-/g, " "),
    monthly: p.monthly_cost,
    annual: p.annual_cost,
    fill: getColor(p.monthly_cost),
  }));

  const savings = cheapest && yourModel
    ? cheapest.annual_cost - yourModel.annual_cost
    : 0;

  return (
    <Card className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-violet-500" />
          <h3 className="text-sm font-semibold uppercase tracking-wider">
            Model Cost Comparison
          </h3>
        </div>
        {savings > 0 && (
          <Badge className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/10">
            Save ${savings.toLocaleString()}/year vs cheapest paid
          </Badge>
        )}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
          <XAxis
            type="number"
            tickFormatter={(v) => `$${v.toLocaleString()}`}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
          />
          <YAxis
            dataKey="name"
            type="category"
            width={140}
            tick={{ fill: "hsl(var(--foreground))", fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(value, name) => [
              `$${Number(value).toLocaleString()}`,
              name === "monthly" ? "Monthly" : "Annual",
            ] as [string, string]}
          />
          <Bar dataKey="monthly" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, idx) => (
              <Cell key={idx} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded" style={{ background: COLORS.free }} />
          <span>Free / Self-hosted</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded" style={{ background: COLORS.cheap }} />
          <span>Under $100/mo</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded" style={{ background: COLORS.mid }} />
          <span>$100-$1K/mo</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded" style={{ background: COLORS.expensive }} />
          <span>Over $1K/mo</span>
        </div>
      </div>
    </Card>
  );
}