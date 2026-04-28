"use client";

import { Table, Layers, AlertTriangle, CheckCircle2, type LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import type { DatasetProfile } from "@/types/profiler";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  color: string;
}

function StatCard({ icon: Icon, label, value, color }: StatCardProps) {
  return (
    <Card className="relative overflow-hidden p-5">
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

interface StatsCardsProps {
  profile: DatasetProfile;
}

export function StatsCards({ profile }: StatsCardsProps) {
  const qualityIssues = Object.values(profile.columns).filter(
    (col) => col.missing_pct > 5
  ).length;

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <StatCard
        icon={Table}
        label="Rows"
        value={profile.num_rows.toLocaleString()}
        color="bg-violet-500"
      />
      <StatCard
        icon={Layers}
        label="Columns"
        value={profile.num_columns}
        color="bg-cyan-500"
      />
      <StatCard
        icon={AlertTriangle}
        label="Quality Issues"
        value={qualityIssues}
        color="bg-amber-500"
      />
      <StatCard
        icon={CheckCircle2}
        label="Quality Score"
        value={`${profile.quality_score}%`}
        color="bg-emerald-500"
      />
    </div>
  );
}