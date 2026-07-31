import { useEffect, useMemo, useState } from "react";

import { createRun, getScenarios, recordDecision } from "./api";
import { percent, shortDigest } from "./format";
import type { EvaluationRun, Scenario } from "./types";

function MetricCard({
  label,
  champion,
  candidate,
}: {
  label: string;
  champion: number;
  candidate: number;
}) {
  const change = candidate - champion;
  return (
    <article className="metric-card">
      <p>{label}</p>
      <strong>{percent(candidate)}</strong>
      <span className={change >= 0 ? "positive" : "negative"}>
        {change >= 0 ? "+" : ""}
        {percent(change)} versus champion
      </span>
    </article>
  );
}

export function App() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scenarioId, setScenarioId] = useState("clean-release");
  const [run, setRun] = useState<EvaluationRun | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");

  useEffect(() => {
    getScenarios()
      .then(setScenarios)
      .catch((caught: unknown) =>
        setError(caught instanceof Error ? caught.message : "Could not load scenarios"),
      );
  }, []);

  const selected = useMemo(
    () => scenarios.find((scenario) => scenario.scenario_id === scenarioId),
    [scenarioId, scenarios],
  );

  async function runEvaluation() {
    setBusy(true);
    setError("");
    try {
      setRun(await createRun(scenarioId));
      setReason("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Evaluation failed");
    } finally {
      setBusy(false);
    }
  }

  async function decide(action: "override" | "reject" | "rollback") {
    if (!run) return;
    setBusy(true);
    setError("");
    try {
      setRun(await recordDecision(run.run_id, action, reason));
      setReason("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Decision could not be recorded");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <header className="site-header">
        <div>
          <p className="eyebrow">Synthetic evaluation workbench</p>
          <h1>Model Release Lab</h1>
          <p className="lede">
            Compare a candidate with the current model, inspect every release gate, and
            keep the decision separate from the score.
          </p>
        </div>
        <a href="https://github.com/charlielucas/model-release-lab">
          View source
        </a>
      </header>

      <main id="main-content">
        <section className="control-panel" aria-labelledby="scenario-heading">
          <div>
            <p className="section-kicker">Guided scenario</p>
            <h2 id="scenario-heading">Choose the failure you want to test</h2>
            <p>{selected?.question ?? "Loading scenarios..."}</p>
          </div>
          <div className="control-row">
            <label>
              Scenario
              <select
                value={scenarioId}
                disabled={busy}
                onChange={(event) => {
                  setScenarioId(event.target.value);
                  setRun(null);
                  setError("");
                }}
              >
                {scenarios.map((scenario) => (
                  <option key={scenario.scenario_id} value={scenario.scenario_id}>
                    {scenario.name}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" onClick={runEvaluation} disabled={busy || !selected}>
              {busy ? "Running checks..." : "Run comparison"}
            </button>
          </div>
          <p className="boundary-note">
            The records, labels, failure fixtures, and reviewer decisions are synthetic.
            This demo makes no external model calls and accepts no uploads.
          </p>
        </section>

        {error && <p className="error" role="alert">{error}</p>}

        {!run && (
          <section className="empty-state">
            <h2>Start with the clean release</h2>
            <p>
              You will see champion and candidate metrics, protected slices, release gates,
              the review queue, and the reproducible evidence fingerprint.
            </p>
          </section>
        )}

        {run && (
          <div className="results" aria-live="polite">
            <section className={`decision-banner decision-${run.current_decision.toLowerCase()}`}>
              <div>
                <p className="section-kicker">Release decision</p>
                <h2>{run.current_decision}</h2>
                <p>{run.question}</p>
              </div>
              <div className="decision-count">
                <strong>{run.gates.filter((gate) => gate.passed).length}/{run.gates.length}</strong>
                <span>gates passed</span>
              </div>
            </section>

            <section aria-labelledby="metrics-heading">
              <div className="section-heading">
                <div>
                  <p className="section-kicker">Model comparison</p>
                  <h2 id="metrics-heading">Candidate versus champion</h2>
                </div>
                <p>{run.candidate_version}</p>
              </div>
              <div className="metric-grid">
                <MetricCard
                  label="Topic accuracy"
                  champion={run.champion_metrics.topic_accuracy}
                  candidate={run.candidate_metrics.topic_accuracy}
                />
                <MetricCard
                  label="Risk accuracy"
                  champion={run.champion_metrics.risk_accuracy}
                  candidate={run.candidate_metrics.risk_accuracy}
                />
                <article className="metric-card">
                  <p>Review rate</p>
                  <strong>{percent(run.candidate_metrics.review_rate)}</strong>
                  <span>{run.review_items.length} records routed to review</span>
                </article>
              </div>
            </section>

            <section aria-labelledby="gates-heading">
              <div className="section-heading">
                <div>
                  <p className="section-kicker">Policy</p>
                  <h2 id="gates-heading">Release gates</h2>
                </div>
                <p>Metrics are measured first. Policy decides what passes.</p>
              </div>
              <div className="gate-list">
                {run.gates.map((gate) => (
                  <article key={gate.gate_id} className={gate.passed ? "gate-pass" : "gate-fail"}>
                    <span aria-hidden="true">{gate.passed ? "✓" : "×"}</span>
                    <div>
                      <h3>{gate.label}</h3>
                      <p>{gate.reason}</p>
                    </div>
                    <div className="gate-measure">
                      <strong>{gate.measured}</strong>
                      <span>{gate.threshold}</span>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section aria-labelledby="slices-heading">
              <div className="section-heading">
                <div>
                  <p className="section-kicker">Protected views</p>
                  <h2 id="slices-heading">Performance by segment</h2>
                </div>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Segment</th>
                      <th scope="col">Rows</th>
                      <th scope="col">Champion topic</th>
                      <th scope="col">Candidate topic</th>
                      <th scope="col">Candidate risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {run.slice_metrics.map((slice) => (
                      <tr key={slice.segment}>
                        <th scope="row">{slice.segment}</th>
                        <td>{slice.count}</td>
                        <td>{percent(slice.champion_topic_accuracy)}</td>
                        <td>{percent(slice.candidate_topic_accuracy)}</td>
                        <td>{percent(slice.candidate_risk_accuracy)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section aria-labelledby="review-heading">
              <div className="section-heading">
                <div>
                  <p className="section-kicker">Human review</p>
                  <h2 id="review-heading">Review queue</h2>
                </div>
                <p>{run.review_items.length} of 20 records</p>
              </div>
              <div className="review-list">
                {run.review_items.slice(0, 8).map((item) => (
                  <article key={item.doc_id}>
                    <div className="review-meta">
                      <strong>{item.doc_id}</strong>
                      <span>{item.segment}</span>
                      <span>{percent(item.candidate_confidence)} confidence</span>
                    </div>
                    <p>{item.text}</p>
                    <dl>
                      <div><dt>Expected</dt><dd>{item.expected_topic} / {item.expected_risk}</dd></div>
                      <div><dt>Candidate</dt><dd>{item.candidate_topic} / {item.candidate_risk}</dd></div>
                    </dl>
                    <p className="reason-list">{item.reasons.join(" / ")}</p>
                  </article>
                ))}
              </div>
              {run.review_items.length > 8 && (
                <p className="queue-limit">
                  Showing the first 8 of {run.review_items.length} review records. The JSON
                  evidence includes the full queue.
                </p>
              )}
            </section>

            <section className="decision-panel" aria-labelledby="decision-heading">
              <div>
                <p className="section-kicker">Bounded action</p>
                <h2 id="decision-heading">Record a decision</h2>
                <p>Overrides and rollbacks require a reason and stay in the run history.</p>
              </div>
              <label>
                Decision reason
                <textarea
                  value={reason}
                  maxLength={300}
                  onChange={(event) => setReason(event.target.value)}
                  placeholder="Explain the evidence behind this decision."
                />
              </label>
              <div className="decision-actions">
                {run.current_decision === "BLOCK" && (
                  <>
                    <button type="button" onClick={() => decide("override")} disabled={busy || !reason.trim()}>
                      Override block
                    </button>
                    <button className="secondary" type="button" onClick={() => decide("reject")} disabled={busy || !reason.trim()}>
                      Reject candidate
                    </button>
                  </>
                )}
                {(run.current_decision === "PASS" || run.current_decision === "OVERRIDE") && (
                  <button className="secondary" type="button" onClick={() => decide("rollback")} disabled={busy || !reason.trim()}>
                    Record rollback
                  </button>
                )}
              </div>
              {run.decision_log.length > 0 && (
                <ol className="decision-log">
                  {run.decision_log.map((event) => (
                    <li key={event.recorded_at}>
                      <strong>{event.result}</strong> {event.reason}
                    </li>
                  ))}
                </ol>
              )}
            </section>

            <section className="evidence-panel" aria-labelledby="evidence-heading">
              <div>
                <p className="section-kicker">Reproducibility</p>
                <h2 id="evidence-heading">Evidence manifest</h2>
              </div>
              <dl>
                <div><dt>Benchmark</dt><dd><code>{shortDigest(run.benchmark_digest)}</code></dd></div>
                <div><dt>Policy</dt><dd><code>{shortDigest(run.policy_digest)}</code></dd></div>
                <div><dt>Candidate</dt><dd><code>{shortDigest(run.candidate_artifact_digest)}</code></dd></div>
                <div><dt>Evaluation</dt><dd><code>{shortDigest(run.evaluation_fingerprint)}</code></dd></div>
              </dl>
              <a className="button-link" href={`/api/runs/${run.run_id}/evidence`} download>
                Download JSON evidence
              </a>
            </section>
          </div>
        )}
      </main>

      <footer>
        <p>Educational release-gating demo. Synthetic data only. Not a production model registry.</p>
      </footer>
    </>
  );
}
