"""Pydantic schemas for cost analyzer endpoints."""

from pydantic import BaseModel, Field


class CostCalculateRequest(BaseModel):
    model: str
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)


class CostCalculateResponse(BaseModel):
    model: str
    input_cost: float
    output_cost: float
    total_cost: float
    supported: bool


class ProjectionRequest(BaseModel):
    daily_calls: int = Field(..., gt=0)
    avg_input_tokens: int = Field(..., gt=0)
    avg_output_tokens: int = Field(..., gt=0)
    models: list[str] | None = None


class ModelProjection(BaseModel):
    model: str
    daily_cost: float
    monthly_cost: float
    annual_cost: float
    input_pricing_per_1m: float
    output_pricing_per_1m: float


class ProjectionResponse(BaseModel):
    projections: list[ModelProjection]


class GrowthPoint(BaseModel):
    month: int
    cost: float


class GrowthResponse(BaseModel):
    points: list[GrowthPoint]


class UsageSummary(BaseModel):
    period_days: int
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    success_rate: float


class ModelInfo(BaseModel):
    name: str
    input_per_1m: float
    output_per_1m: float
    self_hosted: bool


class ModelListResponse(BaseModel):
    models: list[ModelInfo]