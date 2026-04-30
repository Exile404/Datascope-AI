"""Evaluator endpoints — single eval and multi-temperature comparison."""

from fastapi import APIRouter, HTTPException, Request

from app.services.evaluator_service import EvaluatorService
from app.models.evaluator_schema import (
    EvaluateRequest, CompareRequest, CompareResponse, EvaluationResult
)


router = APIRouter(prefix="/evaluator", tags=["evaluator"])


def _service(request: Request) -> EvaluatorService:
    return EvaluatorService(
        llm=request.app.state.llm,
        metrics=request.app.state.metrics,
    )


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate(request: Request, body: EvaluateRequest):
    try:
        service = _service(request)
        result = await service.evaluate_single(
            prompt=body.prompt,
            system=body.system,
            temperature=body.temperature,
            score=body.score,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")


@router.post("/compare", response_model=CompareResponse)
async def compare(request: Request, body: CompareRequest):
    try:
        service = _service(request)
        results = await service.compare_temperatures(
            prompt=body.prompt,
            system=body.system,
            temperatures=body.temperatures,
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")


@router.get("/history")
async def history(request: Request, limit: int = 50):
    try:
        records = await request.app.state.metrics.get_recent_evaluations(limit=limit)
        return {"records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")