"""Command-line interface for deterministic scenario runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .repository import RunRepository
from .scenarios import SCENARIO_BY_ID
from .service import RunService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Model Release Lab scenario")
    parser.add_argument("scenario", choices=sorted(SCENARIO_BY_ID))
    parser.add_argument("--database", type=Path, default=Path(".data/model-release-lab.db"))
    args = parser.parse_args()
    run = RunService(RunRepository(args.database)).execute(args.scenario)
    print(json.dumps(run, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
