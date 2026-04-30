"""DataScope AI — Backend API entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.router import api_router
from app.engines.llm_engine import LLMEngine
from app.engines.embedding_engine import EmbeddingEngine
from app.engines.metrics_store import MetricsStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("  Starting DataScope AI backend...")

    # LLM
    print(f"  LLM: {settings.OLLAMA_MODEL} @ {settings.OLLAMA_BASE_URL}")
    app.state.llm = LLMEngine(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        timeout=settings.LLM_TIMEOUT,
    )

    # Embeddings (lazy-loaded on first use)
    print(f"  Embeddings: all-MiniLM-L6-v2 (lazy)")
    app.state.embeddings = EmbeddingEngine()

    # Metrics store
    print(f"  Metrics: {settings.METRICS_DB_PATH}")
    app.state.metrics = MetricsStore(db_path=settings.METRICS_DB_PATH)
    await app.state.metrics.init()

    # Health check
    try:
        await app.state.llm.health_check()
        print("  ✓ All systems ready")
    except Exception as e:
        print(f"  ⚠ LLM warmup failed: {e}")
        print(f"  ⚠ Make sure Ollama is running")

    yield
    print("  Shutting down...")


app = FastAPI(
    title="DataScope AI",
    description="Intelligent data analysis platform powered by a fine-tuned LLM",
    version="0.2.0",
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
    return {"name": "DataScope AI", "version": "0.2.0", "status": "ok"}


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