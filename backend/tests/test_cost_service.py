"""Unit tests for CostService.

These tests cover the pure-logic static methods.
The async `actual_usage` method (which needs MetricsStore) is tested separately.
"""

import pytest
from app.services.cost_service import CostService, MODEL_PRICING


class TestCalculateCost:
    """Tests for CostService.calculate_cost()."""

    def test_known_model_returns_correct_cost(self):
        # gpt-4o: $2.50 input, $10.00 output per 1M tokens
        # 1000 input tokens = (1000 / 1_000_000) * 2.50 = 0.0025
        # 500 output tokens = (500 / 1_000_000) * 10.00 = 0.005
        result = CostService.calculate_cost("gpt-4o", 1000, 500)

        assert result["supported"] is True
        assert result["model"] == "gpt-4o"
        assert result["input_cost"] == 0.0025
        assert result["output_cost"] == 0.005
        assert result["total_cost"] == 0.0075

    def test_unsupported_model_returns_zero_cost(self):
        result = CostService.calculate_cost("nonexistent-model-xyz", 1000, 500)

        assert result["supported"] is False
        assert result["total_cost"] == 0.0
        assert result["input_cost"] == 0.0
        assert result["output_cost"] == 0.0

    def test_self_hosted_model_costs_nothing(self):
        # datascope-analyst is the user's own fine-tuned model: $0 pricing
        result = CostService.calculate_cost("datascope-analyst", 1_000_000, 1_000_000)

        assert result["supported"] is True
        assert result["total_cost"] == 0.0

    def test_zero_tokens_returns_zero_cost(self):
        result = CostService.calculate_cost("gpt-4o", 0, 0)

        assert result["supported"] is True
        assert result["total_cost"] == 0.0


class TestProjectCosts:
    """Tests for CostService.project_costs()."""

    def test_default_uses_all_models(self):
        results = CostService.project_costs(
            daily_calls=100,
            avg_input_tokens=500,
            avg_output_tokens=200,
        )

        # All models in MODEL_PRICING should appear in results
        assert len(results) == len(MODEL_PRICING)

    def test_results_sorted_by_monthly_cost_ascending(self):
        results = CostService.project_costs(
            daily_calls=1000,
            avg_input_tokens=500,
            avg_output_tokens=200,
        )

        monthly_costs = [r["monthly_cost"] for r in results]
        assert monthly_costs == sorted(monthly_costs)

    def test_filters_out_unknown_models(self):
        results = CostService.project_costs(
            daily_calls=100,
            avg_input_tokens=500,
            avg_output_tokens=200,
            models=["gpt-4o", "nonexistent-xyz"],
        )

        assert len(results) == 1
        assert results[0]["model"] == "gpt-4o"


class TestListModels:
    """Tests for CostService.list_models()."""

    def test_returns_all_models(self):
        models = CostService.list_models()
        assert len(models) == len(MODEL_PRICING)

    def test_self_hosted_flag_correct(self):
        models = CostService.list_models()
        datascope = next(m for m in models if m["name"] == "datascope-analyst")
        assert datascope["self_hosted"] is True

        gpt4o = next(m for m in models if m["name"] == "gpt-4o")
        assert gpt4o["self_hosted"] is False