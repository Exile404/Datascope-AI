"""LLM engine — direct Ollama API client for fine-tuned model inference."""

import re
import json
import httpx
from typing import AsyncIterator


THINKING_RE = re.compile(r"##\s*Initial Observations\s*\n(.*?)(?=##\s*Analysis|\Z)", re.DOTALL)
ANSWER_RE = re.compile(r"##\s*Analysis\s*\n(.*)", re.DOTALL)


class LLMEngine:
    def __init__(
        self,
        base_url: str,
        model: str,
        temperature: float = 0.3,
        timeout: int = 180,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self.base_url}/api/tags")
            r.raise_for_status()
            tags = r.json().get("models", [])
            available = [m["name"] for m in tags]
            if not any(self.model in name for name in available):
                raise RuntimeError(
                    f"Model '{self.model}' not found. Available: {available}"
                )
        return True

    async def generate(self, system: str, user: str) -> dict:
        """Single-shot generation using Ollama's /api/chat endpoint."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "repeat_penalty": 1.15,
                "num_predict": 2048,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.base_url}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()

        raw = data.get("message", {}).get("content", "")
        return self._parse(raw)

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        """Streaming generation."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "repeat_penalty": 1.15,
                "num_predict": 2048,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

    @staticmethod
    def _parse(raw: str) -> dict:
        thinking_match = THINKING_RE.search(raw)
        answer_match = ANSWER_RE.search(raw)

        thinking = thinking_match.group(1).strip() if thinking_match else None
        answer = answer_match.group(1).strip() if answer_match else raw.strip()

        return {
            "thinking": thinking,
            "answer": answer,
            "raw": raw,
        }