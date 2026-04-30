export interface QualityScores {
  relevance: number;
  coherence: number;
  completeness: number;
  factuality: number;
}

export interface EvaluationResult {
  response: string;
  thinking: string | null;
  answer: string | null;
  scores: QualityScores | null;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  temperature: number;
}

export interface CompareResponse {
  results: EvaluationResult[];
}

export interface EvaluateRequest {
  prompt: string;
  system?: string;
  temperature?: number;
  score?: boolean;
}

export interface CompareRequest {
  prompt: string;
  system?: string;
  temperatures?: number[];
}

export interface EvaluationHistoryRecord {
  id: number;
  timestamp: string;
  prompt: string;
  response: string;
  model: string;
  temperature: number;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  scores: QualityScores | null;
}