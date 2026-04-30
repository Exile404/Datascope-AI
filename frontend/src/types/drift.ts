export interface SemanticDrift {
  centroid_drift: number;
  avg_pairwise_drift: number;
  max_pairwise_drift: number;
  samples_above_threshold: number;
}

export interface OutputStats {
  count: number;
  avg_length: number;
  std_length: number;
  min_length: number;
  max_length: number;
}

export interface DriftAlert {
  level: "critical" | "warning" | "info";
  metric: string;
  message: string;
}

export interface DriftResponse {
  semantic: SemanticDrift | Record<string, never>;
  statistical: Record<string, {
    mean_shift_sigma: number;
    ks_pvalue: number;
    skew_change: number;
  }>;
  output_stats?: OutputStats;
  alerts: DriftAlert[];
}

export interface HallucinationFlag {
  index: number;
  invented_numbers: string[];
  preview: string;
}

export interface HallucinationResponse {
  rate: number;
  flagged_count: number;
  total: number;
  examples: HallucinationFlag[];
  alert: boolean;
}

export interface DriftHistoryPoint {
  timestamp: string;
  value: number;
  metadata?: Record<string, unknown>;
}

export interface DriftHistoryResponse {
  metric: string;
  points: DriftHistoryPoint[];
}

export interface DriftDetectRequest {
  baseline_outputs: string[];
  current_outputs: string[];
  baseline_input_stats?: Record<string, unknown>;
  current_input_stats?: Record<string, unknown>;
}

export interface HallucinationRequest {
  outputs: string[];
  source_context: string;
}