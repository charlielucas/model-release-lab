"""Evaluation helpers for labeled documents."""

from __future__ import annotations


def accuracy(rows: list[dict[str, str]], field: str) -> float:
    if not rows:
        return 0.0
    matches = sum(1 for row in rows if row[field] == "True")
    return matches / len(rows)


def missed_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row["topic_match"] != "True" or row["risk_match"] != "True"
    ]
