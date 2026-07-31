# Testing strategy

The test plan follows the risk of each component rather than aiming for one
headline coverage percentage.

## Unit tests

- deterministic champion and candidate predictions
- overall and per-segment accuracy
- controlled-label validation
- review routing and workload limits
- release gate thresholds
- decision transition rules
- evidence fingerprint stability
- empty benchmarks and duplicate prediction IDs

## Integration tests

- SQLite create, read, list, and update behavior
- bounded SQLite retention
- API scenario execution and evidence retrieval
- bounded validation for unknown scenarios, actions, and long reasons
- override and rollback workflow
- frontend API parsing and metric formatting

## End-to-end and release checks

- run all five guided scenarios and assert the expected pass or block result
- start the packaged API and confirm `/health`
- build the React production bundle
- build and start the container, then smoke-test the same-origin application
- inspect desktop and phone-sized layouts, keyboard flow, focus, and contrast

## Continuous integration

CI installs from frozen lockfiles and runs Python lint, Python tests, frontend
type checking, frontend tests, frontend production build, and a package build.
The container smoke test is kept as a release check because it is slower than
the core pull-request suite.
