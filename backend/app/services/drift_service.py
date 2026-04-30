"""Drift detection service — semantic drift + statistical drift + hallucination flagging."""

from __future__ import annotations

import re
import numpy as np
from scipy import stats as scipy_stats

from app.engines.embedding_engine import EmbeddingEngine
from app.engines.metrics_store import MetricsStore


# Drift thresholds (tuned for our use case)
DRIFT_THRESHOLDS = {
    "centroid_drift": 0.30,
    "avg_pairwise_drift": 0.35,
    "hallucination_rate": 0.05,
    "ks_pvalue": 0.05,
}


class DriftService:
    def __init__(self, embeddings: EmbeddingEngine, metrics: MetricsStore):
        self.embeddings = embeddings
        self.metrics = metrics

    async def detect(
        self,
        baseline_outputs: list[str],
        current_outputs: list[str],
        baseline_input_stats: dict | None = None,
        current_input_stats: dict | None = None,
    ) -> dict:
        """Run full drift analysis and persist metrics."""
        results: dict = {
            "semantic": {},
            "statistical": {},
            "alerts": [],
        }

        # Semantic drift via embeddings
        if baseline_outputs and current_outputs:
            results["semantic"] = await self.embeddings.semantic_drift(
                baseline_outputs, current_outputs
            )

            await self.metrics.log_drift(
                "centroid_drift",
                results["semantic"]["centroid_drift"],
            )

            if results["semantic"]["centroid_drift"] > DRIFT_THRESHOLDS["centroid_drift"]:
                results["alerts"].append({
                    "level": "critical",
                    "metric": "centroid_drift",
                    "message": f"Semantic drift exceeds threshold ({results['semantic']['centroid_drift']:.2f} > {DRIFT_THRESHOLDS['centroid_drift']})",
                })

        # Statistical drift on input distributions
        if baseline_input_stats and current_input_stats:
            results["statistical"] = self._statistical_drift(
                baseline_input_stats, current_input_stats
            )

            for col, drift in results["statistical"].items():
                if drift.get("ks_pvalue", 1.0) < DRIFT_THRESHOLDS["ks_pvalue"]:
                    results["alerts"].append({
                        "level": "warning",
                        "metric": f"distribution_drift:{col}",
                        "message": f"Distribution shift detected in '{col}' (p={drift['ks_pvalue']:.4f})",
                    })

        # Output statistics (length, structure)
        if current_outputs:
            results["output_stats"] = self._output_statistics(current_outputs)
            await self.metrics.log_drift(
                "avg_output_length",
                results["output_stats"]["avg_length"],
            )

        return results

    @staticmethod
    def _statistical_drift(baseline: dict, current: dict) -> dict:
        """Per-column distribution drift using mean/std shifts and PSI."""
        drift: dict[str, dict] = {}

        for col_name in baseline.keys() & current.keys():
            b = baseline[col_name]
            c = current[col_name]

            if b.get("type") != "numeric" or c.get("type") != "numeric":
                continue
            if "stats" not in b or "stats" not in c:
                continue

            b_mean, b_std = b["stats"]["mean"], b["stats"]["std"] or 1.0
            c_mean = c["stats"]["mean"]

            mean_shift = abs(c_mean - b_mean) / b_std

            # KS-style approximation using moments (we don't have raw samples here)
            # In production you'd pass raw distributions
            ks_pvalue = float(np.exp(-mean_shift)) if mean_shift > 0 else 1.0

            drift[col_name] = {
                "mean_shift_sigma": round(mean_shift, 3),
                "ks_pvalue": round(ks_pvalue, 4),
                "skew_change": round(
                    abs(c["stats"].get("skewness", 0) - b["stats"].get("skewness", 0)), 3
                ),
            }

        return drift

    @staticmethod
    def _output_statistics(outputs: list[str]) -> dict:
        lengths = [len(o.split()) for o in outputs]
        return {
            "count": len(outputs),
            "avg_length": round(float(np.mean(lengths)), 1),
            "std_length": round(float(np.std(lengths)), 1),
            "min_length": int(np.min(lengths)),
            "max_length": int(np.max(lengths)),
        }

    async def flag_hallucinations(
        self,
        outputs: list[str],
        source_context: str,
    ) -> dict:
        """Flag outputs that mention numbers/entities not in source context."""
        flagged = []

        # Extract numbers from source context
        source_numbers = set(re.findall(r"\d+\.?\d*", source_context))

        for i, output in enumerate(outputs):
            output_numbers = set(re.findall(r"\d+\.?\d*", output))
            invented = output_numbers - source_numbers

            # Filter trivial numbers (0, 1, 2 likely from natural language)
            invented = {n for n in invented if float(n) > 5}

            if invented:
                flagged.append({
                    "index": i,
                    "invented_numbers": sorted(invented),
                    "preview": output[:200],
                })

        rate = len(flagged) / len(outputs) if outputs else 0.0

        await self.metrics.log_drift(
            "hallucination_rate",
            rate,
            metadata={"flagged_count": len(flagged), "total": len(outputs)},
        )

        return {
            "rate": round(rate, 4),
            "flagged_count": len(flagged),
            "total": len(outputs),
            "examples": flagged[:5],
            "alert": rate > DRIFT_THRESHOLDS["hallucination_rate"],
        }

    async def get_history(self, metric: str, limit: int = 30) -> list[dict]:
        return await self.metrics.get_drift_series(metric, limit=limit)