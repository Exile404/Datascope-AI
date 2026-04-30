import { API_ENDPOINTS } from "./constants";
import type {
  DriftResponse,
  HallucinationResponse,
  DriftHistoryResponse,
  DriftDetectRequest,
  HallucinationRequest,
} from "@/types/drift";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export async function detectDrift(body: DriftDetectRequest): Promise<DriftResponse> {
  const res = await fetch(API_ENDPOINTS.DRIFT_DETECT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function flagHallucinations(
  body: HallucinationRequest
): Promise<HallucinationResponse> {
  const res = await fetch(API_ENDPOINTS.DRIFT_HALLUCINATIONS, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function getDriftHistory(
  metric: string,
  limit = 30
): Promise<DriftHistoryResponse> {
  const res = await fetch(`${API_ENDPOINTS.DRIFT_HISTORY(metric)}?limit=${limit}`);
  return handleResponse(res);
}