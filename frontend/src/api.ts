import type { EvaluationRun, Scenario } from "./types";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function getScenarios(): Promise<Scenario[]> {
  return parseResponse<Scenario[]>(await fetch("/api/scenarios"));
}

export async function createRun(scenarioId: string): Promise<EvaluationRun> {
  return parseResponse<EvaluationRun>(
    await fetch("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId }),
    }),
  );
}

export async function recordDecision(
  runId: string,
  action: "override" | "reject" | "rollback",
  reason: string,
): Promise<EvaluationRun> {
  return parseResponse<EvaluationRun>(
    await fetch(`/api/runs/${runId}/decisions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, reason }),
    }),
  );
}
