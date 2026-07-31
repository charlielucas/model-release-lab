export type Scenario = {
  scenario_id: string;
  name: string;
  question: string;
  description: string;
  expected_decision: "PASS" | "BLOCK";
};

export type ModelMetrics = {
  topic_accuracy: number;
  risk_accuracy: number;
  review_rate: number;
  invalid_label_count: number;
};

export type Gate = {
  gate_id: string;
  label: string;
  passed: boolean;
  measured: string;
  threshold: string;
  reason: string;
};

export type SliceMetric = {
  segment: string;
  count: number;
  champion_topic_accuracy: number;
  candidate_topic_accuracy: number;
  champion_risk_accuracy: number;
  candidate_risk_accuracy: number;
};

export type ReviewItem = {
  doc_id: string;
  segment: string;
  text: string;
  expected_topic: string;
  expected_risk: string;
  champion_topic: string;
  candidate_topic: string;
  champion_risk: string;
  candidate_risk: string;
  candidate_confidence: number;
  reasons: string[];
};

export type DecisionEvent = {
  action: string;
  result: string;
  reason: string;
  recorded_at: string;
};

export type EvaluationRun = {
  run_id: string;
  created_at: string;
  scenario_id: string;
  scenario_name: string;
  question: string;
  description: string;
  benchmark_digest: string;
  policy_digest: string;
  evaluation_fingerprint: string;
  champion_version: string;
  candidate_version: string;
  champion_artifact_digest: string;
  candidate_artifact_digest: string;
  champion_metrics: ModelMetrics;
  candidate_metrics: ModelMetrics;
  slice_metrics: SliceMetric[];
  gates: Gate[];
  review_items: ReviewItem[];
  initial_decision: "PASS" | "BLOCK";
  current_decision: string;
  decision_log: DecisionEvent[];
};
