export interface CostCalculation {
  model: string;
  input_cost: number;
  output_cost: number;
  total_cost: number;
  supported: boolean;
}

export interface ModelProjection {
  model: string;
  daily_cost: number;
  monthly_cost: number;
  annual_cost: number;
  input_pricing_per_1m: number;
  output_pricing_per_1m: number;
}

export interface ProjectionRequest {
  daily_calls: number;
  avg_input_tokens: number;
  avg_output_tokens: number;
  models?: string[];
}

export interface UsageSummary {
  period_days: number;
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  success_rate: number;
}

export interface ModelInfo {
  name: string;
  input_per_1m: number;
  output_per_1m: number;
  self_hosted: boolean;
}

export interface GrowthPoint {
  month: number;
  cost: number;
}