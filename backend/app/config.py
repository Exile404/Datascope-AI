

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # ── CORS ──
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",      # Next.js dev
        "http://127.0.0.1:3000",
    ]

    # ── LLM (Ollama) ──
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "datascope-analyst"
    LLM_TEMPERATURE: float = 0.3
    LLM_TIMEOUT: int = 120                # seconds

    # ── File upload limits ──
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_ROWS: int = 100_000               # cap CSV rows for safety

    # ── Profiler ──
    CORRELATION_THRESHOLD: float = 0.3    # only show correlations above this


settings = Settings()