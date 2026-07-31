from pathlib import Path

import httpx
import pytest

from model_release_lab.api import create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def api_client(database_path: Path) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app(database_path))
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.anyio
async def test_api_workflow_and_evidence_download(tmp_path: Path) -> None:
    async with api_client(tmp_path / "api.db") as client:
        scenarios = await client.get("/api/scenarios")
        assert scenarios.status_code == 200
        assert len(scenarios.json()) == 5

        created = await client.post("/api/runs", json={"scenario_id": "schema-violation"})
        assert created.status_code == 201
        run_id = created.json()["run_id"]

        fetched = await client.get(f"/api/runs/{run_id}")
        evidence = await client.get(f"/api/runs/{run_id}/evidence")
        assert fetched.status_code == 200
        assert evidence.status_code == 200
        assert evidence.headers["content-disposition"].startswith("attachment;")
        assert evidence.json()["evaluation_fingerprint"] == fetched.json()["evaluation_fingerprint"]


@pytest.mark.anyio
async def test_api_rejects_unknown_or_unbounded_inputs(tmp_path: Path) -> None:
    async with api_client(tmp_path / "api.db") as client:
        unknown = await client.post("/api/runs", json={"scenario_id": "not-a-scenario"})
        missing = await client.get("/api/runs/not-a-run")
        oversized = await client.post(
            "/api/runs/not-a-run/decisions",
            json={"action": "override", "reason": "x" * 301},
        )

        assert unknown.status_code == 404
        assert missing.status_code == 404
        assert oversized.status_code == 422


@pytest.mark.anyio
async def test_api_records_bounded_override_and_rollback(tmp_path: Path) -> None:
    async with api_client(tmp_path / "api.db") as client:
        response = await client.post("/api/runs", json={"scenario_id": "override-and-rollback"})
        run = response.json()

        override = await client.post(
            f"/api/runs/{run['run_id']}/decisions",
            json={"action": "override", "reason": "Reviewed for the synthetic exercise."},
        )
        rollback = await client.post(
            f"/api/runs/{run['run_id']}/decisions",
            json={"action": "rollback", "reason": "Protected-slice evidence is unresolved."},
        )

        assert override.status_code == 200
        assert override.json()["current_decision"] == "OVERRIDE"
        assert rollback.status_code == 200
        assert rollback.json()["current_decision"] == "ROLLED_BACK"


@pytest.mark.anyio
async def test_health_and_cors_are_explicit(tmp_path: Path) -> None:
    async with api_client(tmp_path / "api.db") as client:
        health = await client.get("/health")
        preflight = await client.options(
            "/api/runs",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )

        assert health.json() == {"status": "ok"}
        assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert health.headers["x-content-type-options"] == "nosniff"
        assert health.headers["x-frame-options"] == "DENY"


@pytest.mark.anyio
async def test_compiled_frontend_uses_explicit_runtime_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frontend = tmp_path / "compiled-frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<h1>Packaged interface</h1>", encoding="utf-8")
    (frontend / "favicon.svg").write_text("<svg></svg>", encoding="utf-8")
    monkeypatch.setenv("MODEL_RELEASE_LAB_FRONTEND", str(frontend))

    async with api_client(tmp_path / "api.db") as client:
        root = await client.get("/")
        favicon = await client.get("/favicon.svg")

        assert root.status_code == 200
        assert "Packaged interface" in root.text
        assert favicon.status_code == 200
        assert favicon.headers["content-type"].startswith("image/svg+xml")
