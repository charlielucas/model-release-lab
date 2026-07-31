# Model Release Lab

[Try the live demo](https://model-release-lab.onrender.com/)

Model Release Lab is a small, full-stack workbench for deciding whether a text
classifier is ready to replace the current model. It compares a transparent
rules champion with a TF-IDF and logistic-regression candidate, then applies
release policy separately from model scoring.

The project uses only synthetic records. It accepts no uploads, makes no remote
model calls, and contains no employer or customer data.

## Why I built it

A model can improve overall while getting worse on an important slice. It can
also create an unsustainable review queue, emit unexpected labels, or need a
documented exception after the metrics are complete. Those are release
problems, not just model-training problems.

This project turns that workflow into something you can inspect:

- champion and candidate metrics on the same benchmark
- separate topic and risk-label accuracy
- protected Security-segment checks
- controlled-label and review-workload gates
- record-level review reasons
- required explanations for overrides, rejections, and rollbacks
- reproducible model, benchmark, policy, and evaluation fingerprints

## Guided scenarios

| Scenario | What it proves | Expected result |
| --- | --- | --- |
| Clean release | The candidate clears every configured gate | PASS |
| Critical slice regression | Aggregate results cannot hide a Security regression | BLOCK |
| Unknown label | Outputs outside the controlled taxonomy stop the release | BLOCK |
| Review workload surge | Confidence drift cannot silently overwhelm reviewers | BLOCK |
| Override and rollback | Human decisions are bounded and recorded after evaluation | BLOCK, then reviewer action |

Each failure is an explicit, versioned fixture. The interface labels synthetic
injections instead of presenting them as organic model behavior.

The review queue is benchmark analysis, so it can route known candidate misses
as well as low-confidence outputs. It is not a claim about live production
review volume, and the displayed probability is not separately calibrated.

## Stack

- Python 3.11, scikit-learn, FastAPI, SQLite
- React 19, TypeScript, Vite
- pytest, Ruff, Vitest
- Docker and GitHub Actions

The evaluation engine is independent of HTTP and persistence. FastAPI handles
validated requests, SQLite stores complete run evidence, and the React client
shows the same API used by the tests. See [the architecture notes](docs/ARCHITECTURE.md)
and [testing strategy](docs/TESTING.md) for the boundaries and tradeoffs.

## Run locally

Install [uv](https://docs.astral.sh/uv/) and Node.js 22, then run:

```bash
make install
make check
```

Start the API and UI in separate terminals:

```bash
make dev-api
make dev-ui
```

Open `http://localhost:5173`. You can also run one scenario without the web UI:

```bash
uv run model-release-lab clean-release
```

## Run the container

```bash
docker build -t model-release-lab .
docker run --rm -p 8000:8000 model-release-lab
```

Open `http://localhost:8000`. The container compiles the frontend and serves it
from the same FastAPI process.

## Deploy

The included `render.yaml` defines one free Docker web service with `/health` as
its health check. Render sets the public port at runtime, so the same image also
runs locally on port 8000. Run history uses the service's ephemeral filesystem
and can reset when a free instance sleeps, restarts, or redeploys.

The public demo runs on Render's free tier, so the first request after a period
of inactivity can take about a minute.

## Boundaries

This is an educational release workflow, not a production model registry. The
benchmark is deliberately small, SQLite is appropriate only for a single demo
process, and reviewer identity is not authenticated. A production version would
need durable object storage, signed model and dataset versions, reviewer roles,
background jobs, migrations, and production monitoring.
