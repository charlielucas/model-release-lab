from pathlib import Path

import pytest

from model_release_lab.data import BENCHMARK_DOCUMENTS
from model_release_lab.evaluation import evaluate_run
from model_release_lab.repository import RunRepository
from model_release_lab.scenarios import SCENARIO_BY_ID
from model_release_lab.service import RunService


@pytest.fixture
def service(tmp_path: Path) -> RunService:
    return RunService(RunRepository(tmp_path / "runs.db"))


@pytest.mark.parametrize(
    ("scenario_id", "expected"),
    [
        ("clean-release", "PASS"),
        ("critical-slice-regression", "BLOCK"),
        ("schema-violation", "BLOCK"),
        ("review-surge", "BLOCK"),
        ("override-and-rollback", "BLOCK"),
    ],
)
def test_guided_scenarios_reach_expected_decision(
    service: RunService, scenario_id: str, expected: str
) -> None:
    run = service.execute(scenario_id)

    assert run["initial_decision"] == expected
    assert run["current_decision"] == expected
    assert run["evaluation_fingerprint"]


def test_same_scenario_has_reproducible_evaluation(service: RunService) -> None:
    first = service.execute("clean-release")
    second = service.execute("clean-release")

    assert first["run_id"] != second["run_id"]
    assert first["evaluation_fingerprint"] == second["evaluation_fingerprint"]
    assert first["candidate_metrics"] == second["candidate_metrics"]
    assert len(first["champion_artifact_digest"]) == 64
    assert len(first["candidate_artifact_digest"]) == 64


def test_evaluation_rejects_empty_or_duplicate_benchmarks(service: RunService) -> None:
    scenario = SCENARIO_BY_ID["clean-release"]
    documents = list(BENCHMARK_DOCUMENTS)
    champion_predictions = service.champion.predict(documents)
    candidate_predictions = service.candidate.predict(documents)

    with pytest.raises(ValueError, match="at least one"):
        evaluate_run(
            scenario,
            [],
            [],
            [],
            service.policy,
            service.champion.artifact_digest,
            service.candidate.artifact_digest,
        )

    with pytest.raises(ValueError, match="exactly once"):
        evaluate_run(
            scenario,
            documents,
            champion_predictions + [champion_predictions[0]],
            candidate_predictions,
            service.policy,
            service.champion.artifact_digest,
            service.candidate.artifact_digest,
        )


def test_critical_slice_cannot_hide_behind_aggregate(service: RunService) -> None:
    run = service.execute("critical-slice-regression")
    gates = {gate["gate_id"]: gate for gate in run["gates"]}
    failed_gates = {gate_id for gate_id, gate in gates.items() if not gate["passed"]}

    assert gates["critical-slice"]["passed"] is False
    assert failed_gates == {"critical-slice"}
    assert any(item["segment"] == "Security" for item in run["review_items"])


def test_unmapped_candidate_label_is_blocked(service: RunService) -> None:
    run = service.execute("schema-violation")
    gates = {gate["gate_id"]: gate for gate in run["gates"]}
    failed_gates = {gate_id for gate_id, gate in gates.items() if not gate["passed"]}

    assert run["candidate_metrics"]["invalid_label_count"] == 1
    assert gates["valid-labels"]["passed"] is False
    assert failed_gates == {"valid-labels"}


def test_review_surge_is_blocked_by_workload_gate(service: RunService) -> None:
    run = service.execute("review-surge")
    gates = {gate["gate_id"]: gate for gate in run["gates"]}
    failed_gates = {gate_id for gate_id, gate in gates.items() if not gate["passed"]}

    assert gates["review-rate"]["passed"] is False
    assert failed_gates == {"review-rate"}
    assert run["candidate_metrics"]["review_rate"] == 1.0


def test_override_requires_reason_and_rollback_follows_override(service: RunService) -> None:
    run = service.execute("override-and-rollback")

    with pytest.raises(ValueError, match="1 to 300"):
        service.decide(run["run_id"], "override", "")

    overridden = service.decide(
        run["run_id"], "override", "Synthetic reviewer accepts the bounded risk."
    )
    rolled_back = service.decide(
        run["run_id"], "rollback", "The protected slice remains below its release floor."
    )

    assert overridden["current_decision"] == "OVERRIDE"
    assert rolled_back["current_decision"] == "ROLLED_BACK"
    assert [event["action"] for event in rolled_back["decision_log"]] == [
        "override",
        "rollback",
    ]


def test_passed_run_cannot_be_overridden(service: RunService) -> None:
    run = service.execute("clean-release")

    with pytest.raises(ValueError, match="not allowed from PASS"):
        service.decide(run["run_id"], "override", "No override is needed.")


def test_terminal_decision_cannot_be_reopened(service: RunService) -> None:
    run = service.execute("override-and-rollback")
    rejected = service.decide(run["run_id"], "reject", "Candidate misses the slice gate.")

    with pytest.raises(ValueError, match="not allowed from REJECTED"):
        service.decide(rejected["run_id"], "override", "Try to reopen the decision.")
