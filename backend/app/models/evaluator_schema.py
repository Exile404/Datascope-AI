"""Pydantic schemas for evaluator endpoints."""

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to evaluate")
    system: str = Field(default="You are a helpful assistant.")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    score: bool = Field(default=True, description="Run LLM-as-judge scoring")


class CompareRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to compare across temperatures")
    system: str = Field(default="You are a helpful assistant.")
    temperatures: list[float] = Field(default=[0.1, 0.5, 0.9])


class QualityScores(BaseModel):
    relevance: int = Field(..., ge=0, le=100)
    coherence: int = Field(..., ge=0, le=100)
    completeness: int = Field(..., ge=0, le=100)
    factuality: int = Field(..., ge=0, le=100)


class EvaluationResult(BaseModel):
    response: str
    thinking: str | None = None
    answer: str | None = None
    scores: QualityScores | None = None
    latency_ms: int
    input_tokens: int
    output_tokens: int
    temperature: float


class CompareResponse(BaseModel):
    results: list[EvaluationResult]