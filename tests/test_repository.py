from pathlib import Path

from model_release_lab.repository import RunRepository


def test_repository_round_trip_and_update(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / "runs.db")
    run = {
        "run_id": "run-1",
        "created_at": "2026-07-31T00:00:00+00:00",
        "scenario_id": "clean-release",
        "current_decision": "PASS",
    }
    repository.save(run)
    run["current_decision"] = "ROLLED_BACK"
    repository.save(run)

    assert repository.get("run-1") == run
    assert repository.list() == [run]
    assert repository.get("missing") is None


def test_repository_prunes_old_runs(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / "runs.db", max_runs=2)
    for index in range(3):
        repository.save(
            {
                "run_id": f"run-{index}",
                "created_at": f"2026-07-31T00:00:0{index}+00:00",
                "scenario_id": "clean-release",
            }
        )

    assert [run["run_id"] for run in repository.list()] == ["run-2", "run-1"]
    assert repository.get("run-0") is None
