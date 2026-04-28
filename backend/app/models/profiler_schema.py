"""Profiler request/response schemas."""

from typing import Any
from pydantic import BaseModel, Field


class NumericStats(BaseModel):
    mean: float
    std: float
    min: float
    max: float
    median: float
    q25: float
    q75: float
    skewness: float
    kurtosis: float
    outliers: int
    outlier_pct: float


class ColumnProfile(BaseModel):
    name: str
    type: str
    missing: int
    missing_pct: float
    unique_values: int
    unique_ratio: float
    stats: NumericStats | None = None
    top_values: dict[str, int] | None = None
    imbalance_ratio: float | None = None


class CorrelationPair(BaseModel):
    col1: str
    col2: str
    r: float
    strength: str


class DatasetProfile(BaseModel):
    num_rows: int
    num_columns: int
    columns: dict[str, ColumnProfile]
    correlations: list[CorrelationPair]
    quality_score: float


class ProfileResponse(BaseModel):
    dataset_name: str
    profile: DatasetProfile


class InsightResponse(BaseModel):
    dataset_name: str
    profile: DatasetProfile
    thinking: str | None = Field(None, description="Chain-of-thought reasoning")
    answer: str = Field(..., description="Final analysis")
    raw_output: str = Field(..., description="Unparsed LLM output")