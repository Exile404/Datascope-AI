"""Statistical profiler — analyzes a DataFrame and produces a structured profile."""

import pandas as pd
import numpy as np


CORRELATION_THRESHOLD = 0.3


def profile_dataframe(df: pd.DataFrame) -> dict:
    profile = {
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "columns": {},
        "correlations": [],
        "quality_score": 0.0,
    }

    numeric_cols = []

    for col_name in df.columns:
        series = df[col_name]
        col_profile = _profile_column(col_name, series, len(df))
        profile["columns"][col_name] = col_profile
        if col_profile["type"] == "numeric":
            numeric_cols.append(col_name)

    if len(numeric_cols) >= 2:
        profile["correlations"] = _compute_correlations(df, numeric_cols)

    total_missing = df.isna().sum().sum()
    total_cells = len(df) * len(df.columns)
    missing_pct = (total_missing / total_cells * 100) if total_cells > 0 else 0
    profile["quality_score"] = round(max(0, 100 - missing_pct * 2), 1)

    return profile


def _profile_column(name: str, series: pd.Series, total_rows: int) -> dict:
    missing = int(series.isna().sum())
    missing_pct = round(missing / total_rows * 100, 2) if total_rows else 0

    cp = {
        "name": name,
        "missing": missing,
        "missing_pct": missing_pct,
        "unique_values": int(series.nunique()),
        "unique_ratio": round(series.nunique() / total_rows, 4) if total_rows else 0,
    }

    if pd.api.types.is_numeric_dtype(series):
        cp["type"] = "numeric"
        clean = series.dropna()
        if len(clean) > 0:
            cp["stats"] = _numeric_stats(clean)
    else:
        cp["type"] = "categorical"
        vc = series.value_counts()
        cp["top_values"] = {str(k): int(v) for k, v in vc.head(5).items()}
        if len(vc) > 1:
            cp["imbalance_ratio"] = round(float(vc.iloc[0] / vc.iloc[-1]), 2)

    return cp


def _numeric_stats(clean: pd.Series) -> dict:
    q1 = float(clean.quantile(0.25))
    q3 = float(clean.quantile(0.75))
    iqr = q3 - q1
    outliers = int(((clean < q1 - 1.5 * iqr) | (clean > q3 + 1.5 * iqr)).sum())

    return {
        "mean": round(float(clean.mean()), 4),
        "std": round(float(clean.std()), 4) if len(clean) > 1 else 0.0,
        "min": round(float(clean.min()), 4),
        "max": round(float(clean.max()), 4),
        "median": round(float(clean.median()), 4),
        "q25": round(q1, 4),
        "q75": round(q3, 4),
        "skewness": round(float(clean.skew()), 4) if len(clean) > 2 else 0.0,
        "kurtosis": round(float(clean.kurtosis()), 4) if len(clean) > 3 else 0.0,
        "outliers": outliers,
        "outlier_pct": round(outliers / len(clean) * 100, 2),
    }


def _compute_correlations(df: pd.DataFrame, numeric_cols: list[str]) -> list[dict]:
    corr = df[numeric_cols].corr()
    results = []

    for i, c1 in enumerate(numeric_cols):
        for j, c2 in enumerate(numeric_cols):
            if i >= j:
                continue
            r = float(corr.loc[c1, c2])
            if pd.isna(r) or abs(r) < CORRELATION_THRESHOLD:
                continue
            r = round(r, 4)
            strength = (
                "strong" if abs(r) > 0.7
                else "moderate" if abs(r) > 0.5
                else "weak"
            )
            results.append({"col1": c1, "col2": c2, "r": r, "strength": strength})

    return sorted(results, key=lambda x: -abs(x["r"]))


def format_profile_as_prompt(profile: dict, dataset_name: str = "Uploaded Dataset") -> str:
    """Format profile into the exact text format the LLM was trained on."""
    lines = [
        f"Dataset: {dataset_name}",
        f"Rows: {profile['num_rows']:,} | Columns: {profile['num_columns']}",
        f"Quality Score: {profile['quality_score']}%",
        "",
        "=== Column Profiles ===",
    ]

    for col_name, col in profile["columns"].items():
        line = f"- {col_name} ({col['type']}): {col['unique_values']} unique"
        if col["missing_pct"] > 0:
            line += f", {col['missing_pct']}% missing"

        if col["type"] == "numeric" and "stats" in col:
            s = col["stats"]
            line += (
                f" | mean={s['mean']}, std={s['std']}, median={s['median']}, "
                f"range=[{s['min']}, {s['max']}], skew={s['skewness']}, "
                f"kurtosis={s['kurtosis']}"
            )
            if s["outlier_pct"] > 0:
                line += f", outliers={s['outlier_pct']}%"
        elif col["type"] == "categorical" and "top_values" in col:
            top = ", ".join(f"{k}:{v}" for k, v in list(col["top_values"].items())[:4])
            line += f" | top: [{top}]"
            if "imbalance_ratio" in col:
                line += f", imbalance_ratio={col['imbalance_ratio']}"

        lines.append(line)

    if profile["correlations"]:
        lines.extend(["", "=== Notable Correlations ==="])
        for c in profile["correlations"]:
            lines.append(f"- {c['col1']} ↔ {c['col2']}: r={c['r']} ({c['strength']})")

    return "\n".join(lines)