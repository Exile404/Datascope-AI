"""Evaluator service — LLM-as-judge scoring + multi-temperature comparison."""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Literal

from app.engines.llm_engine import LLMEngine
from app.engines.metrics_store import MetricsStore


JUDGE_PROMPT = """You are an evaluator. Score the response below on four dimensions.

Original prompt:
{prompt}

Response to score:
{response}

Score each dimension from 0-100 (integer):
- relevance: Does it address the prompt directly?
- coherence: Is it logically structured and well-written?
- completeness: Does it cover the key aspects expected?
- factuality: Are statements grounded in the prompt context, not invented?

Return ONLY valid JSON in this exact format, no other text:
{{"relevance": <int>, "coherence": <int>, "completeness": <int>, "factuality": <int>}}"""


SCORE_KEYS = ["relevance", "coherence", "completeness", "factuality"]


class EvaluatorService:
    def __init__(self, llm: LLMEngine, metrics: MetricsStore):
        self.llm = llm
        self.metrics = metrics

    async def evaluate_single(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        temperature: float = 0.3,
        score: bool = True,
    ) -> dict:
        """Run a single inference and optionally score it."""
        start = time.time()
        result = await self.llm.generate(system, prompt, temperature=temperature)
        latency_ms = int((time.time() - start) * 1000)

        response = result["raw"]
        scores = await self._judge(prompt, response) if score else None

        # Token estimates (model doesn't always return exact counts)
        input_tokens = len(prompt.split()) + len(system.split())
        output_tokens = len(response.split())

        await self.metrics.log_evaluation(
            prompt=prompt,
            response=response,
            model=self.llm.model,
            temperature=temperature,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            scores=scores,
        )

        return {
            "response": response,
            "thinking": result.get("thinking"),
            "answer": result.get("answer"),
            "scores": scores,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "temperature": temperature,
        }

    async def compare_temperatures(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        temperatures: list[float] | None = None,
    ) -> list[dict]:
        """Run the same prompt across multiple temperatures and score each."""
        temperatures = temperatures or [0.1, 0.5, 0.9]
        tasks = [
            self.evaluate_single(prompt, system, temp, score=True)
            for temp in temperatures
        ]
        return await asyncio.gather(*tasks)

    async def _judge(self, prompt: str, response: str) -> dict[str, int]:
        """Use the LLM as a judge to score a response."""
        judge_prompt = JUDGE_PROMPT.format(
            prompt=prompt[:1000], response=response[:2000]
        )

        try:
            result = await self.llm.generate(
                system="You are an objective evaluator. Output only JSON.",
                user=judge_prompt,
                temperature=0.1,
            )
            scores = self._parse_scores(result["raw"])
            return scores
        except Exception:
            return {k: 0 for k in SCORE_KEYS}

    @staticmethod
    def _parse_scores(raw: str) -> dict[str, int]:
        match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
        if not match:
            return {k: 0 for k in SCORE_KEYS}

        try:
            parsed = json.loads(match.group(0))
            return {
                k: int(parsed.get(k, 0))
                for k in SCORE_KEYS
            }
        except (json.JSONDecodeError, ValueError, TypeError):
            return {k: 0 for k in SCORE_KEYS}