"""API router — mounts all endpoint groups."""

from fastapi import APIRouter

from app.api import profiler


api_router = APIRouter()
api_router.include_router(profiler.router)