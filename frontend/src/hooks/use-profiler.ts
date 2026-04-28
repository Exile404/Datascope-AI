"use client";

import { useMutation } from "@tanstack/react-query";
import { getInsight, profileCSV } from "@/lib/api-client";
import type { InsightResponse, ProfileResponse } from "@/types/profiler";

export function useInsight() {
  return useMutation<InsightResponse, Error, { file: File; datasetName?: string }>({
    mutationFn: ({ file, datasetName }) => getInsight(file, datasetName),
  });
}

export function useProfile() {
  return useMutation<ProfileResponse, Error, File>({
    mutationFn: (file) => profileCSV(file),
  });
}