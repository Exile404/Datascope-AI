import { API_ENDPOINTS } from "./constants";
import type {
  EvaluationResult,
  CompareResponse,
  EvaluateRequest,
  CompareRequest,
  EvaluationHistoryRecord,
} from "@/types/evaluator";

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

export async function evaluatePrompt(body: EvaluateRequest): Promise<EvaluationResult> {
  const res = await fetch(API_ENDPOINTS.EVAL_SINGLE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function comparePrompt(body: CompareRequest): Promise<CompareResponse> {
  const res = await fetch(API_ENDPOINTS.EVAL_COMPARE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function getEvalHistory(limit = 50): Promise<{ records: EvaluationHistoryRecord[] }> {
  const res = await fetch(`${API_ENDPOINTS.EVAL_HISTORY}?limit=${limit}`);
  return handleResponse(res);
}