"""
DataScope AI — Backend API
FastAPI server that orchestrates data profiling and LLM insight generation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.router import api_router
from app.core.llm_engine import LLMEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: warm up the LLM. Shutdown: cleanup."""
    print(f"  Starting DataScope AI backend...")
    print(f"  LLM endpoint: {settings.OLLAMA_BASE_URL}")
    print(f"  Model: {settings.OLLAMA_MODEL}")

    app.state.llm = LLMEngine(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=settings.LLM_TEMPERATURE,
    )

    try:
        await app.state.llm.health_check()
        print(f"  ✓ LLM ready")
    except Exception as e:
        print(f"  ⚠ LLM warmup failed: {e}")
        print(f"  ⚠ Make sure Ollama is running: ollama serve")

    yield
    print("  Shutting down...")


app = FastAPI(
    title="DataScope AI",
    description="Intelligent data analysis platform powered by a fine-tuned LLM",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"name": "DataScope AI", "version": "0.1.0", "status": "ok"}


@app.get("/health")
async def health():
    llm_status = "unknown"
    try:
        await app.state.llm.health_check()
        llm_status = "ok"
    except Exception:
        llm_status = "down"
    return {"api": "ok", "llm": llm_status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )