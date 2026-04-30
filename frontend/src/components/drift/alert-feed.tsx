"use client";

import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { DriftAlert } from "@/types/drift";

interface AlertFeedProps {
  alerts: DriftAlert[];
}

const ALERT_CONFIG = {
  critical: { icon: AlertCircle, color: "text-red-500", bg: "bg-red-500/5", border: "border-red-500/40" },
  warning: { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-500/5", border: "border-amber-500/40" },
  info: { icon: Info, color: "text-cyan-500", bg: "bg-cyan-500/5", border: "border-cyan-500/40" },
};

export function AlertFeed({ alerts }: AlertFeedProps) {
  if (alerts.length === 0) {
    return (
      <Card className="border-emerald-500/30 bg-emerald-500/5 p-5">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/20">
            <Info className="h-4 w-4 text-emerald-500" />
          </div>
          <div>
            <p className="text-sm font-medium">All systems normal</p>
            <p className="text-xs text-muted-foreground">No drift alerts detected</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert, i) => {
        const config = ALERT_CONFIG[alert.level] || ALERT_CONFIG.info;
        const Icon = config.icon;
        return (
          <Card
            key={i}
            className={`${config.bg} ${config.border} p-4`}
          >
            <div className="flex items-start gap-3">
              <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${config.color}`} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={`${config.color} border-current text-[10px] uppercase`}
                  >
                    {alert.level}
                  </Badge>
                  <span className="font-mono text-xs text-muted-foreground">
                    {alert.metric}
                  </span>
                </div>
                <p className="mt-1.5 text-sm">{alert.message}</p>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}