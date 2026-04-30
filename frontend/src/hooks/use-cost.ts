"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { projectCosts, getUsage, getModels } from "@/lib/api-cost";
import type { ProjectionRequest } from "@/types/cost";

export function useProjections() {
  return useMutation({
    mutationFn: (body: ProjectionRequest) => projectCosts(body),
  });
}

export function useUsage(days: number = 30) {
  return useQuery({
    queryKey: ["usage", days],
    queryFn: () => getUsage(days),
  });
}

export function useModels() {
  return useQuery({
    queryKey: ["models"],
    queryFn: () => getModels(),
    staleTime: Infinity,
  });
}