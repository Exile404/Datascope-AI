"""Drift monitor endpoints — detect, flag, query history."""

from fastapi import APIRouter, HTTPException, Request

from app.services.drift_service import DriftService
from app.models.drift_schema import (
    DriftDetectRequest, DriftResponse,
    HallucinationRequest, HallucinationResponse,
    DriftHistoryResponse,
)


router = APIRouter(prefix="/drift", tags=["drift"])


def _service(request: Request) -> DriftService:
    return DriftService(
        embeddings=request.app.state.embeddings,
        metrics=request.app.state.metrics,
    )


@router.post("/detect", response_model=DriftResponse)
async def detect(request: Request, body: DriftDetectRequest):
    try:
        service = _service(request)
        return await service.detect(
            baseline_outputs=body.baseline_outputs,
            current_outputs=body.current_outputs,
            baseline_input_stats=body.baseline_input_stats,
            current_input_stats=body.current_input_stats,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drift detection failed: {e}")


@router.post("/hallucinations", response_model=HallucinationResponse)
async def flag_hallucinations(request: Request, body: HallucinationRequest):
    try:
        service = _service(request)
        return await service.flag_hallucinations(
            outputs=body.outputs,
            source_context=body.source_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hallucination check failed: {e}")


@router.get("/history/{metric}", response_model=DriftHistoryResponse)
async def history(request: Request, metric: str, limit: int = 30):
    try:
        service = _service(request)
        points = await service.get_history(metric, limit=limit)
        return {"metric": metric, "points": points}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")