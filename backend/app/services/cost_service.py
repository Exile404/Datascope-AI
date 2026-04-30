"""Cost service — token cost calculations and projections across LLM providers."""

from __future__ import annotations

from app.engines.metrics_store import MetricsStore


# Pricing per 1M tokens (USD), as of April 2026
# Update this table as providers change pricing
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Anthropic
    "claude-opus-4-7": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 0.8, "output": 4.0},

    # OpenAI
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "o1-preview": {"input": 15.0, "output": 60.0},

    # Google
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.3},

    # Meta (via providers like Together AI)
    "llama-3.1-70b": {"input": 0.88, "output": 0.88},
    "llama-3.1-8b": {"input": 0.18, "output": 0.18},

    # Self-hosted (your model — only electricity + amortization)
    "datascope-analyst": {"input": 0.0, "output": 0.0},
}


class CostService:
    def __init__(self, metrics: MetricsStore):
        self.metrics = metrics

    @staticmethod
    def calculate_cost(
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> dict:
        """Compute cost for a single call."""
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            return {
                "model": model,
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "supported": False,
            }

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return {
            "model": model,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(input_cost + output_cost, 6),
            "supported": True,
        }

    @staticmethod
    def project_costs(
        daily_calls: int,
        avg_input_tokens: int,
        avg_output_tokens: int,
        models: list[str] | None = None,
    ) -> list[dict]:
        """Project monthly/annual costs across multiple models."""
        models = models or list(MODEL_PRICING.keys())

        results = []
        for model in models:
            pricing = MODEL_PRICING.get(model)
            if not pricing:
                continue

            daily_input = (daily_calls * avg_input_tokens / 1_000_000) * pricing["input"]
            daily_output = (daily_calls * avg_output_tokens / 1_000_000) * pricing["output"]
            daily_total = daily_input + daily_output

            results.append({
                "model": model,
                "daily_cost": round(daily_total, 2),
                "monthly_cost": round(daily_total * 30, 2),
                "annual_cost": round(daily_total * 365, 2),
                "input_pricing_per_1m": pricing["input"],
                "output_pricing_per_1m": pricing["output"],
            })

        return sorted(results, key=lambda x: x["monthly_cost"])

    @staticmethod
    def project_growth(
        base_monthly_cost: float,
        growth_rate: float = 0.08,
        months: int = 12,
    ) -> list[dict]:
        """Project costs over N months with compounding growth."""
        return [
            {
                "month": i + 1,
                "cost": round(base_monthly_cost * ((1 + growth_rate) ** i), 2),
            }
            for i in range(months)
        ]

    async def actual_usage(self, days: int = 30) -> dict:
        """Real usage from metrics store."""
        summary = await self.metrics.get_usage_summary(days=days)
        return {
            "period_days": days,
            "total_calls": summary.get("total_calls") or 0,
            "total_input_tokens": summary.get("total_input_tokens") or 0,
            "total_output_tokens": summary.get("total_output_tokens") or 0,
            "total_cost_usd": round(summary.get("total_cost") or 0.0, 4),
            "avg_latency_ms": round(summary.get("avg_latency_ms") or 0.0, 1),
            "success_rate": (
                (summary.get("successful_calls") or 0) / (summary.get("total_calls") or 1)
            ),
        }

    @staticmethod
    def list_models() -> list[dict]:
        """All supported models with their pricing."""
        return [
            {
                "name": name,
                "input_per_1m": pricing["input"],
                "output_per_1m": pricing["output"],
                "self_hosted": pricing["input"] == 0.0 and pricing["output"] == 0.0,
            }
            for name, pricing in MODEL_PRICING.items()
        ]