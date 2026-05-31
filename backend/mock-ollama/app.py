"""Ollama API mock for staging environment.

Fakes the two endpoints that LLMEngine actually calls:
  - GET  /api/tags   -> list of available models
  - POST /api/chat   -> generation response

Response schemas match Ollama 0.6.x exactly so the backend can't tell
the difference at the HTTP level.

This mock is used in staging only. Production talks to real Ollama.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


# Model name we'll advertise. Must match the OLLAMA_MODEL the backend asks for.
MOCK_MODEL_NAME = os.getenv("MOCK_MODEL_NAME", "datascope-analyst:latest")

# Deterministic canned response. Mirrors the format LLMEngine._parse() expects:
# headers "## Initial Observations" and "## Analysis".
CANNED_RESPONSE = (
    "## Initial Observations\n"
    "This is a mocked response from the staging Ollama service. "
    "The dataset would normally be analysed here, but for CI/CD testing "
    "we return a fixed payload so that integration tests are deterministic.\n"
    "\n"
    "## Analysis\n"
    "- Mock environment: staging\n"
    "- No real model inference performed\n"
    "- Use docker-compose.prod.yml for actual LLM responses\n"
)


app = FastAPI(
    title="Ollama Mock",
    description="Staging-only mock of the Ollama API for DataScope AI CI/CD",
    version="1.0.0",
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    options: dict | None = None


@app.get("/")
async def root():
    return {"service": "ollama-mock", "status": "ok"}


@app.get("/api/tags")
async def list_models():
    """Mirrors Ollama's model-list endpoint."""
    return {
        "models": [
            {
                "name": MOCK_MODEL_NAME,
                "modified_at": datetime.now(timezone.utc).isoformat(),
                "size": 0,
                "digest": "mock-digest",
                "details": {
                    "format": "gguf",
                    "family": "llama",
                    "parameter_size": "8B",
                    "quantization_level": "Q4_K_M",
                },
            }
        ]
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Mirrors Ollama's /api/chat endpoint.

    Supports both stream=False (single JSON) and stream=True (NDJSON chunks).
    """
    if not req.stream:
        return {
            "model": req.model,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "message": {"role": "assistant", "content": CANNED_RESPONSE},
            "done": True,
            "total_duration": 1_000_000,
            "load_duration": 0,
            "prompt_eval_count": 42,
            "eval_count": 100,
        }

    # Streaming: yield one word at a time to mimic real Ollama behaviour
    async def event_stream():
        words = CANNED_RESPONSE.split(" ")
        for i, word in enumerate(words):
            chunk = {
                "model": req.model,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "message": {"role": "assistant", "content": word + " "},
                "done": i == len(words) - 1,
            }
            yield json.dumps(chunk) + "\n"
            await asyncio.sleep(0.005)  # tiny delay so streaming feels real

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
