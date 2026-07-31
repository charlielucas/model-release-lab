"""Small SQLite repository for synthetic evaluation runs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class RunRepository:
    def __init__(self, path: Path, max_runs: int = 200) -> None:
        if max_runs < 1:
            raise ValueError("max_runs must be positive")
        self.path = path
        self.max_runs = max_runs
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def save(self, run: dict[str, Any]) -> None:
        payload = json.dumps(run, sort_keys=True, separators=(",", ":"))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO runs (run_id, created_at, scenario_id, payload_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET payload_json = excluded.payload_json
                """,
                (run["run_id"], run["created_at"], run["scenario_id"], payload),
            )
            connection.execute(
                """
                DELETE FROM runs
                WHERE run_id NOT IN (
                    SELECT run_id FROM runs
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT ?
                )
                """,
                (self.max_runs,),
            )

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]
