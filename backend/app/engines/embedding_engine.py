"""Sentence embedding engine — used for semantic drift detection and similarity scoring."""

from __future__ import annotations

import asyncio
import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL = "all-MiniLM-L6-v2"


class EmbeddingEngine:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self._lock = asyncio.Lock()

    async def _load(self) -> SentenceTransformer:
        if self._model is None:
            async with self._lock:
                if self._model is None:
                    loop = asyncio.get_event_loop()
                    self._model = await loop.run_in_executor(
                        None, SentenceTransformer, self.model_name
                    )
        return self._model

    async def embed(self, text: str | list[str]) -> np.ndarray:
        model = await self._load()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: model.encode(text, normalize_embeddings=True)
        )

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    @staticmethod
    def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
        return 1.0 - EmbeddingEngine.cosine_similarity(a, b)

    async def semantic_drift(self, baseline: list[str], current: list[str]) -> dict:
        """Measure how far current outputs have drifted from baseline."""
        baseline_emb = await self.embed(baseline)
        current_emb = await self.embed(current)

        baseline_centroid = baseline_emb.mean(axis=0)
        current_centroid = current_emb.mean(axis=0)

        centroid_drift = self.cosine_distance(baseline_centroid, current_centroid)

        # Pairwise drift — average distance from each current to nearest baseline
        pairwise_drifts = []
        for c in current_emb:
            min_dist = min(self.cosine_distance(c, b) for b in baseline_emb)
            pairwise_drifts.append(min_dist)

        return {
            "centroid_drift": round(float(centroid_drift), 4),
            "avg_pairwise_drift": round(float(np.mean(pairwise_drifts)), 4),
            "max_pairwise_drift": round(float(np.max(pairwise_drifts)), 4),
            "samples_above_threshold": int(np.sum(np.array(pairwise_drifts) > 0.3)),
        }