"""Pydantic schemas for drift monitor endpoints."""

from typing import Any
from pydantic import BaseModel, Field


class DriftDetectRequest(BaseModel):
    baseline_outputs: list[str] = Field(..., min_length=1)
    current_outputs: list[str] = Field(..., min_length=1)
    baseline_input_stats: dict[str, Any] | None = None
    current_input_stats: dict[str, Any] | None = None


class HallucinationRequest(BaseModel):
    outputs: list[str] = Field(..., min_length=1)
    source_context: str = Field(..., min_length=1)


class DriftAlert(BaseModel):
    level: str
    metric: str
    message: str


class SemanticDrift(BaseModel):
    centroid_drift: float = 0.0
    avg_pairwise_drift: float = 0.0
    max_pairwise_drift: float = 0.0
    samples_above_threshold: int = 0


class OutputStats(BaseModel):
    count: int
    avg_length: float
    std_length: float
    min_length: int
    max_length: int


class DriftResponse(BaseModel):
    semantic: SemanticDrift | dict = {}
    statistical: dict[str, Any] = {}
    output_stats: OutputStats | dict = {}
    alerts: list[DriftAlert] = []


class HallucinationFlag(BaseModel):
    index: int
    invented_numbers: list[str]
    preview: str


class HallucinationResponse(BaseModel):
    rate: float
    flagged_count: int
    total: int
    examples: list[HallucinationFlag]
    alert: bool


class DriftHistoryPoint(BaseModel):
    timestamp: str
    value: float
    metadata: dict[str, Any] | None = None


class DriftHistoryResponse(BaseModel):
    metric: str
    points: list[DriftHistoryPoint]