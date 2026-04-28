export interface NumericStats {
  mean: number;
  std: number;
  min: number;
  max: number;
  median: number;
  q25: number;
  q75: number;
  skewness: number;
  kurtosis: number;
  outliers: number;
  outlier_pct: number;
}

export interface ColumnProfile {
  name: string;
  type: "numeric" | "categorical";
  missing: number;
  missing_pct: number;
  unique_values: number;
  unique_ratio: number;
  stats: NumericStats | null;
  top_values: Record<string, number> | null;
  imbalance_ratio: number | null;
}

export interface CorrelationPair {
  col1: string;
  col2: string;
  r: number;
  strength: "weak" | "moderate" | "strong";
}

export interface DatasetProfile {
  num_rows: number;
  num_columns: number;
  columns: Record<string, ColumnProfile>;
  correlations: CorrelationPair[];
  quality_score: number;
}

export interface ProfileResponse {
  dataset_name: string;
  profile: DatasetProfile;
}

export interface InsightResponse {
  dataset_name: string;
  profile: DatasetProfile;
  thinking: string | null;
  answer: string;
  raw_output: string;
}