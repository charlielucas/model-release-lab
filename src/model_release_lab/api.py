"""FastAPI surface for Model Release Lab."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .repository import RunRepository
from .scenarios import SCENARIOS
from .service import RunService


class RunRequest(BaseModel):
    scenario_id: str = Field(min_length=1, max_length=80)


class DecisionRequest(BaseModel):
    action: str = Field(pattern="^(override|reject|rollback)$")
    reason: str = Field(min_length=1, max_length=300)


def create_app(database_path: Path | None = None) -> FastAPI:
    resolved_database = database_path or Path(
        os.environ.get("MODEL_RELEASE_LAB_DB", ".data/model-release-lab.db")
    )
    service = RunService(RunRepository(resolved_database))
    app = FastAPI(
        title="Model Release Lab API",
        version="0.1.0",
        description="Synthetic model evaluation and release-gating service.",
    )
    app.state.service = service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/scenarios")
    def scenarios() -> list[dict[str, str]]:
        return [
            {
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "question": scenario.question,
                "description": scenario.description,
                "expected_decision": scenario.expected_decision,
            }
            for scenario in SCENARIOS
        ]

    @app.get("/api/runs")
    def runs() -> list[dict[str, object]]:
        return service.repository.list()

    @app.post("/api/runs", status_code=201)
    def create_run(request: RunRequest) -> dict[str, object]:
        try:
            return service.execute(request.scenario_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Unknown scenario") from error

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, object]:
        run = service.repository.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    @app.post("/api/runs/{run_id}/decisions")
    def decide(run_id: str, request: DecisionRequest) -> dict[str, object]:
        try:
            return service.decide(run_id, request.action, request.reason)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Run not found") from error
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/api/runs/{run_id}/evidence")
    def evidence(run_id: str) -> JSONResponse:
        run = service.repository.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return JSONResponse(
            content=run,
            headers={"Content-Disposition": f'attachment; filename="model-release-{run_id}.json"'},
        )

    frontend_dist = Path(os.environ.get("MODEL_RELEASE_LAB_FRONTEND", "frontend/dist")).resolve()
    if frontend_dist.exists():
        assets = frontend_dist / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str) -> FileResponse:
            requested = frontend_dist / path
            if path and requested.is_file() and frontend_dist in requested.resolve().parents:
                return FileResponse(requested)
            return FileResponse(frontend_dist / "index.html")

    return app


app = create_app()
