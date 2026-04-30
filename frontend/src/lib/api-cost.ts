import { API_ENDPOINTS } from "./constants";
import type {
  CostCalculation,
  ModelProjection,
  ProjectionRequest,
  UsageSummary,
  ModelInfo,
  GrowthPoint,
} from "@/types/cost";

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

export async function calculateCost(
  model: string,
  inputTokens: number,
  outputTokens: number
): Promise<CostCalculation> {
  const res = await fetch(API_ENDPOINTS.COST_CALCULATE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
    }),
  });
  return handleResponse(res);
}

export async function projectCosts(
  body: ProjectionRequest
): Promise<{ projections: ModelProjection[] }> {
  const res = await fetch(API_ENDPOINTS.COST_PROJECT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function getGrowth(
  baseMonthlyCost: number,
  growthRate = 0.08,
  months = 12
): Promise<{ points: GrowthPoint[] }> {
  const url = `${API_ENDPOINTS.COST_GROWTH}?base_monthly_cost=${baseMonthlyCost}&growth_rate=${growthRate}&months=${months}`;
  const res = await fetch(url);
  return handleResponse(res);
}

export async function getUsage(days = 30): Promise<UsageSummary> {
  const res = await fetch(`${API_ENDPOINTS.COST_USAGE}?days=${days}`);
  return handleResponse(res);
}

export async function getModels(): Promise<{ models: ModelInfo[] }> {
  const res = await fetch(API_ENDPOINTS.COST_MODELS);
  return handleResponse(res);
}