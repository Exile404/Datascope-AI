"""Cost analyzer endpoints — calculate, project, query usage."""

from fastapi import APIRouter, HTTPException, Request

from app.services.cost_service import CostService
from app.models.cost_schema import (
    CostCalculateRequest, CostCalculateResponse,
    ProjectionRequest, ProjectionResponse,
    GrowthResponse, UsageSummary, ModelListResponse,
)


router = APIRouter(prefix="/cost", tags=["cost"])


def _service(request: Request) -> CostService:
    return CostService(metrics=request.app.state.metrics)


@router.post("/calculate", response_model=CostCalculateResponse)
async def calculate(body: CostCalculateRequest):
    return CostService.calculate_cost(
        model=body.model,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
    )


@router.post("/project", response_model=ProjectionResponse)
async def project(body: ProjectionRequest):
    projections = CostService.project_costs(
        daily_calls=body.daily_calls,
        avg_input_tokens=body.avg_input_tokens,
        avg_output_tokens=body.avg_output_tokens,
        models=body.models,
    )
    return {"projections": projections}


@router.get("/growth", response_model=GrowthResponse)
async def growth(base_monthly_cost: float, growth_rate: float = 0.08, months: int = 12):
    points = CostService.project_growth(
        base_monthly_cost=base_monthly_cost,
        growth_rate=growth_rate,
        months=months,
    )
    return {"points": points}


@router.get("/usage", response_model=UsageSummary)
async def usage(request: Request, days: int = 30):
    try:
        service = _service(request)
        return await service.actual_usage(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch usage: {e}")


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    return {"models": CostService.list_models()}