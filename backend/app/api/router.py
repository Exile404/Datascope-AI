"""API router — mounts all endpoint groups."""

from fastapi import APIRouter

from app.api import profiler, evaluator, drift, cost


api_router = APIRouter()
api_router.include_router(profiler.router)
api_router.include_router(evaluator.router)
api_router.include_router(drift.router)
api_router.include_router(cost.router)