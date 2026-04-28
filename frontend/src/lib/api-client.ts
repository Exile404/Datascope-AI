import { API_ENDPOINTS } from "./constants";
import type { ProfileResponse, InsightResponse } from "@/types/profiler";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export async function profileCSV(file: File): Promise<ProfileResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(API_ENDPOINTS.PROFILE, {
    method: "POST",
    body: formData,
  });
  return handleResponse<ProfileResponse>(res);
}

export async function getInsight(
  file: File,
  datasetName?: string
): Promise<InsightResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (datasetName) formData.append("dataset_name", datasetName);

  const res = await fetch(API_ENDPOINTS.INSIGHT, {
    method: "POST",
    body: formData,
  });
  return handleResponse<InsightResponse>(res);
}

export async function checkHealth(): Promise<{ api: string; llm: string }> {
  const res = await fetch(API_ENDPOINTS.HEALTH);
  return handleResponse(res);
}

export { ApiError };