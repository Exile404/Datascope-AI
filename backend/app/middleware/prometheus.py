"""Prometheus metrics middleware.

Exposes:
- http_requests_total{method, handler, status}    Counter
- http_request_duration_seconds{method, handler}  Histogram
- http_requests_in_progress{method, handler}      Gauge

Endpoint: GET /metrics (Prometheus text exposition format).

Toggle via env var ENABLE_METRICS=true. When false, middleware
is a no-op and /metrics returns 404.
"""
from __future__ import annotations

import os
import time
from typing import Callable

from fastapi import FastAPI, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Excluded paths: never instrument these (self-scrape, health probes).
EXCLUDED_PATHS = {"/metrics", "/health"}

# Latency buckets in seconds (Prometheus default + LLM-friendly extras).
LATENCY_BUCKETS = (
    0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5,
    1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0,
)


def _route_template(request: Request) -> str:
    """Return the FastAPI route template, e.g. /api/users/{id}.

    Falls back to "unmatched" for 404s to avoid cardinality blow-up.
    """
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return "unmatched"


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, registry: CollectorRegistry) -> None:
        super().__init__(app)
        self.requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests.",
            labelnames=("method", "handler", "status"),
            registry=registry,
        )
        self.request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency (seconds).",
            labelnames=("method", "handler"),
            buckets=LATENCY_BUCKETS,
            registry=registry,
        )
        self.in_progress = Gauge(
            "http_requests_in_progress",
            "In-flight HTTP requests.",
            labelnames=("method", "handler"),
            registry=registry,
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path in EXCLUDED_PATHS:
            return await call_next(request)

        method = request.method
        # We don't know the template until the route is matched, but
        # call_next populates request.scope["route"] before returning.
        start = time.perf_counter()
        handler = path  # provisional; refined post-dispatch
        in_progress = self.in_progress.labels(method=method, handler=handler)
        in_progress.inc()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            elapsed = time.perf_counter() - start
            handler = _route_template(request)
            self.requests_total.labels(
                method=method, handler=handler, status=str(status)
            ).inc()
            self.request_duration.labels(
                method=method, handler=handler
            ).observe(elapsed)
            in_progress.dec()


def setup_metrics(app: FastAPI) -> None:
    """Attach Prometheus middleware and /metrics endpoint to the app.

    No-op when ENABLE_METRICS is not truthy. Idempotent (safe to call once).
    """
    if os.getenv("ENABLE_METRICS", "").lower() not in ("1", "true", "yes"):
        return

    registry = CollectorRegistry()
    app.add_middleware(PrometheusMiddleware, registry=registry)

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(
            content=generate_latest(registry),
            media_type=CONTENT_TYPE_LATEST,
        )
