"""Profiler endpoints — CSV upload and analysis."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.config import settings
from app.services.insight_service import InsightService, SYSTEM_PROMPT
from app.services.profiler_service import profile_dataframe, format_profile_as_prompt
from app.models.profiler_schema import ProfileResponse, InsightResponse

import io
import pandas as pd


router = APIRouter(prefix="/profiler", tags=["profiler"])


def _validate_upload(file: UploadFile, file_bytes: bytes):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported",
        )

    size_mb = len(file_bytes) / 1024 / 1024
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({size_mb:.1f} MB). Max: {settings.MAX_UPLOAD_SIZE_MB} MB",
        )


def _parse_csv(file_bytes: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV: {e}",
        )

    if len(df) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV is empty",
        )

    if len(df) > settings.MAX_ROWS:
        df = df.sample(n=settings.MAX_ROWS, random_state=42)

    return df


@router.post("/profile", response_model=ProfileResponse)
async def profile_csv(file: UploadFile = File(...)):
    """Profile a CSV: returns statistics only (no LLM analysis)."""
    file_bytes = await file.read()
    _validate_upload(file, file_bytes)

    df = _parse_csv(file_bytes)
    profile = profile_dataframe(df)

    return {
        "dataset_name": file.filename,
        "profile": profile,
    }


@router.post("/insight", response_model=InsightResponse)
async def analyze_csv(
    request: Request,
    file: UploadFile = File(...),
    dataset_name: str | None = Form(None),
):
    """Profile + LLM analysis: full insight pipeline."""
    file_bytes = await file.read()
    _validate_upload(file, file_bytes)

    name = dataset_name or file.filename
    service = InsightService(llm=request.app.state.llm, max_rows=settings.MAX_ROWS)

    try:
        result = await service.analyze_csv(file_bytes, dataset_name=name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    return result


@router.post("/insight/stream")
async def stream_insight(
    request: Request,
    file: UploadFile = File(...),
    dataset_name: str | None = Form(None),
):
    """Streaming version: token-by-token output via Server-Sent Events."""
    file_bytes = await file.read()
    _validate_upload(file, file_bytes)

    df = _parse_csv(file_bytes)
    profile = profile_dataframe(df)
    prompt = format_profile_as_prompt(profile, dataset_name or file.filename)

    llm = request.app.state.llm

    async def event_stream():
        async for chunk in llm.stream(SYSTEM_PROMPT, prompt):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")