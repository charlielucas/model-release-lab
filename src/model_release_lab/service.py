"""Application service for evaluations and bounded reviewer decisions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .data import BENCHMARK_DOCUMENTS, TRAINING_DOCUMENTS
from .evaluation import evaluate_run
from .models import RulesModel, SklearnTextModel, apply_failure_fixture
from .repository import RunRepository
from .scenarios import SCENARIO_BY_ID, ReleasePolicy

DECISION_TRANSITIONS = {
    "BLOCK": {"override": "OVERRIDE", "reject": "REJECTED"},
    "PASS": {"rollback": "ROLLED_BACK"},
    "OVERRIDE": {"rollback": "ROLLED_BACK"},
}


class RunService:
    def __init__(self, repository: RunRepository) -> None:
        self.repository = repository
        self.policy = ReleasePolicy()
        self.champion = RulesModel()
        self.candidate = SklearnTextModel(TRAINING_DOCUMENTS)

    def execute(self, scenario_id: str) -> dict[str, Any]:
        scenario = SCENARIO_BY_ID.get(scenario_id)
        if scenario is None:
            raise KeyError(scenario_id)
        documents = list(BENCHMARK_DOCUMENTS)
        champion_predictions = self.champion.predict(documents)
        candidate_predictions = apply_failure_fixture(
            self.candidate.predict(documents),
            documents,
            scenario.failure_fixture,
        )
        result = evaluate_run(
            scenario,
            documents,
            champion_predictions,
            candidate_predictions,
            self.policy,
            self.champion.artifact_digest,
            self.candidate.artifact_digest,
        )
        run = {
            "run_id": str(uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.name,
            "question": scenario.question,
            "description": scenario.description,
            "expected_decision": scenario.expected_decision,
            **result,
        }
        self.repository.save(run)
        return run

    def decide(self, run_id: str, action: str, reason: str) -> dict[str, Any]:
        run = self.repository.get(run_id)
        if run is None:
            raise KeyError(run_id)
        cleaned_reason = reason.strip()
        if not cleaned_reason or len(cleaned_reason) > 300:
            raise ValueError("Decision reason must contain 1 to 300 characters")
        available_actions = DECISION_TRANSITIONS.get(run["current_decision"], {})
        if action not in available_actions:
            raise ValueError(f"Action '{action}' is not allowed from {run['current_decision']}")

        event = {
            "action": action,
            "result": available_actions[action],
            "reason": cleaned_reason,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        run["decision_log"].append(event)
        run["current_decision"] = event["result"]
        self.repository.save(run)
        return run
