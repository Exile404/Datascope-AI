"""Metrics store — SQLite-backed time-series storage for drift, evaluations, and usage."""

from __future__ import annotations

import json
import aiosqlite
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MetricsStore:
    def __init__(self, db_path: str = "./metrics.db"):
        self.db_path = Path(db_path)

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT NOT NULL,
                    temperature REAL,
                    latency_ms INTEGER,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    scores TEXT
                );

                CREATE TABLE IF NOT EXISTS drift_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS llm_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    cost_usd REAL,
                    success INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_drift_timestamp
                    ON drift_snapshots(timestamp);
                CREATE INDEX IF NOT EXISTS idx_drift_metric
                    ON drift_snapshots(metric_name, timestamp);
                CREATE INDEX IF NOT EXISTS idx_calls_timestamp
                    ON llm_calls(timestamp);
                """
            )
            await db.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def log_evaluation(
        self,
        prompt: str,
        response: str,
        model: str,
        temperature: float | None,
        latency_ms: int,
        input_tokens: int,
        output_tokens: int,
        scores: dict[str, float] | None = None,
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO evaluations
                (timestamp, prompt, response, model, temperature, latency_ms,
                 input_tokens, output_tokens, scores)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._now(), prompt, response, model, temperature,
                    latency_ms, input_tokens, output_tokens,
                    json.dumps(scores) if scores else None,
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def log_drift(
        self,
        metric_name: str,
        metric_value: float,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO drift_snapshots (timestamp, metric_name, metric_value, metadata) VALUES (?, ?, ?, ?)",
                (
                    self._now(), metric_name, metric_value,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def log_llm_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        cost_usd: float | None = None,
        success: bool = True,
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO llm_calls
                (timestamp, model, input_tokens, output_tokens, latency_ms, cost_usd, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._now(), model, input_tokens, output_tokens,
                    latency_ms, cost_usd, 1 if success else 0,
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def get_drift_series(
        self,
        metric_name: str,
        limit: int = 100,
    ) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT timestamp, metric_value, metadata
                FROM drift_snapshots
                WHERE metric_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (metric_name, limit),
            )
            rows = await cursor.fetchall()
            return [
                {
                    "timestamp": r["timestamp"],
                    "value": r["metric_value"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else None,
                }
                for r in reversed(rows)
            ]

    async def get_recent_evaluations(self, limit: int = 50) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM evaluations ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [
                {
                    **dict(r),
                    "scores": json.loads(r["scores"]) if r["scores"] else None,
                }
                for r in rows
            ]

    async def get_usage_summary(self, days: int = 30) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT
                    COUNT(*) as total_calls,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(cost_usd) as total_cost,
                    AVG(latency_ms) as avg_latency_ms,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls
                FROM llm_calls
                WHERE timestamp >= datetime('now', ? || ' days')
                """,
                (f"-{days}",),
            )
            row = await cursor.fetchone()
            return dict(row) if row else {}