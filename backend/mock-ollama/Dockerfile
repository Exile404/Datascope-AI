# syntax=docker/dockerfile:1.7
# Ollama API mock for DataScope AI staging.
# Used by: docker-compose.staging.yml
# Image size target: ~50 MB

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

RUN useradd --create-home --shell /bin/bash --uid 1000 mockuser
USER mockuser

EXPOSE 11434

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:11434/ || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "11434"]
