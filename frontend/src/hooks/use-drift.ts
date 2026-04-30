"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { detectDrift, flagHallucinations, getDriftHistory } from "@/lib/api-drift";
import type { DriftDetectRequest, HallucinationRequest } from "@/types/drift";

export function useDetectDrift() {
  return useMutation({
    mutationFn: (body: DriftDetectRequest) => detectDrift(body),
  });
}

export function useFlagHallucinations() {
  return useMutation({
    mutationFn: (body: HallucinationRequest) => flagHallucinations(body),
  });
}

export function useDriftHistory(metric: string, limit = 30) {
  return useQuery({
    queryKey: ["drift-history", metric, limit],
    queryFn: () => getDriftHistory(metric, limit),
    refetchInterval: 30000,
  });
}