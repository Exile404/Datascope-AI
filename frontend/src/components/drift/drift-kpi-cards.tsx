"use client";

import { Activity, AlertTriangle, TrendingUp, Layers, type LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import type { SemanticDrift, OutputStats } from "@/types/drift";

interface KPICardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  color: string;
  alert?: boolean;
}

function KPICard({ icon: Icon, label, value, color, alert }: KPICardProps) {
  return (
    <Card className={`relative overflow-hidden p-5 ${alert ? "border-red-500/40" : ""}`}>
      <div
        className={`absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-10 ${color}`}
      />
      <div className="relative">
        <Icon className={`h-5 w-5 ${color.replace("bg-", "text-")}`} />
        <div className="mt-3 text-2xl font-bold tracking-tight">{value}</div>
        <div className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">
          {label}
        </div>
      </div>
    </Card>
  );
}

interface DriftKPICardsProps {
  semantic?: SemanticDrift | Record<string, never>;
  outputStats?: OutputStats;
}

export function DriftKPICards({ semantic, outputStats }: DriftKPICardsProps) {
  const sem = semantic && "centroid_drift" in semantic ? semantic : null;
  const centroidDrift = sem?.centroid_drift ?? 0;
  const samplesAbove = sem?.samples_above_threshold ?? 0;
  const avgPairwise = sem?.avg_pairwise_drift ?? 0;
  const avgLength = outputStats?.avg_length ?? 0;

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <KPICard
        icon={Activity}
        label="Centroid Drift"
        value={centroidDrift.toFixed(3)}
        color={centroidDrift > 0.3 ? "bg-red-500" : "bg-violet-500"}
        alert={centroidDrift > 0.3}
      />
      <KPICard
        icon={TrendingUp}
        label="Avg Pairwise Drift"
        value={avgPairwise.toFixed(3)}
        color={avgPairwise > 0.35 ? "bg-red-500" : "bg-cyan-500"}
        alert={avgPairwise > 0.35}
      />
      <KPICard
        icon={AlertTriangle}
        label="Drifted Samples"
        value={samplesAbove}
        color={samplesAbove > 0 ? "bg-amber-500" : "bg-emerald-500"}
      />
      <KPICard
        icon={Layers}
        label="Avg Output Length"
        value={`${avgLength} words`}
        color="bg-cyan-500"
      />
    </div>
  );
}