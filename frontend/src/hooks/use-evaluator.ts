"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { evaluatePrompt, comparePrompt, getEvalHistory } from "@/lib/api-evaluator";
import type { EvaluateRequest, CompareRequest } from "@/types/evaluator";

export function useEvaluate() {
  return useMutation({
    mutationFn: (body: EvaluateRequest) => evaluatePrompt(body),
  });
}

export function useCompare() {
  return useMutation({
    mutationFn: (body: CompareRequest) => comparePrompt(body),
  });
}

export function useEvalHistory(limit = 20) {
  return useQuery({
    queryKey: ["eval-history", limit],
    queryFn: () => getEvalHistory(limit),
    refetchInterval: 30000,
  });
}