"""Insight service — orchestrates profiling and LLM analysis."""

import io
import pandas as pd

from app.core.llm_engine import LLMEngine
from app.services.profiler_service import profile_dataframe, format_profile_as_prompt


SYSTEM_PROMPT = (
    "You are a senior data scientist. Analyze the following dataset profile "
    "and provide a comprehensive insight covering distribution analysis, "
    "correlation findings, data quality assessment, and actionable recommendations. "
    "Structure your response with clear sections."
)


class InsightService:
    def __init__(self, llm: LLMEngine, max_rows: int = 100_000):
        self.llm = llm
        self.max_rows = max_rows

    async def analyze_csv(
        self,
        file_bytes: bytes,
        dataset_name: str = "Uploaded Dataset",
    ) -> dict:
        df = self._parse_csv(file_bytes)
        profile = profile_dataframe(df)
        prompt = format_profile_as_prompt(profile, dataset_name)

        result = await self.llm.generate(SYSTEM_PROMPT, prompt)

        return {
            "dataset_name": dataset_name,
            "profile": profile,
            "prompt": prompt,
            "thinking": result["thinking"],
            "answer": result["answer"],
            "raw_output": result["raw"],
        }

    async def analyze_profile(self, profile: dict, dataset_name: str = "Dataset") -> dict:
        prompt = format_profile_as_prompt(profile, dataset_name)
        result = await self.llm.generate(SYSTEM_PROMPT, prompt)

        return {
            "dataset_name": dataset_name,
            "profile": profile,
            "thinking": result["thinking"],
            "answer": result["answer"],
            "raw_output": result["raw"],
        }

    def _parse_csv(self, file_bytes: bytes) -> pd.DataFrame:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")

        if len(df) == 0:
            raise ValueError("CSV is empty")

        if len(df) > self.max_rows:
            df = df.sample(n=self.max_rows, random_state=42)

        return df