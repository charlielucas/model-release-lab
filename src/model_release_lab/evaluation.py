"""Model comparison, review routing, and release gates."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import asdict

from .domain import (
    CRITICAL_SEGMENT,
    RISK_LABELS,
    TOPIC_LABELS,
    Document,
    GateResult,
    ModelMetrics,
    Prediction,
    ReviewItem,
    SliceMetrics,
    serialize,
)
from .scenarios import ReleasePolicy, Scenario


def _accuracy(
    documents: list[Document],
    predictions: dict[str, Prediction],
    expected_field: str,
    predicted_field: str,
) -> float:
    if not documents:
        return 0.0
    correct = sum(
        getattr(document, expected_field) == getattr(predictions[document.doc_id], predicted_field)
        for document in documents
    )
    return correct / len(documents)


def _invalid_count(predictions: list[Prediction]) -> int:
    return sum(
        prediction.predicted_topic not in TOPIC_LABELS
        or prediction.predicted_risk not in RISK_LABELS
        for prediction in predictions
    )


def _review_reasons(
    document: Document,
    candidate: Prediction,
    policy: ReleasePolicy,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.confidence < policy.review_confidence_threshold:
        reasons.append("low candidate confidence")
    if candidate.predicted_topic != document.expected_topic:
        reasons.append("candidate topic miss")
    if candidate.predicted_risk != document.expected_risk:
        reasons.append("candidate risk miss")
    if candidate.predicted_topic not in TOPIC_LABELS or candidate.predicted_risk not in RISK_LABELS:
        reasons.append("unmapped label")
    return tuple(reasons)


def evaluate_run(
    scenario: Scenario,
    documents: list[Document],
    champion_predictions: list[Prediction],
    candidate_predictions: list[Prediction],
    policy: ReleasePolicy,
    champion_artifact_digest: str,
    candidate_artifact_digest: str,
) -> dict[str, object]:
    if not documents:
        raise ValueError("Benchmark must contain at least one document")
    champion_by_id = {prediction.doc_id: prediction for prediction in champion_predictions}
    candidate_by_id = {prediction.doc_id: prediction for prediction in candidate_predictions}
    expected_ids = {document.doc_id for document in documents}
    if (
        len(champion_predictions) != len(documents)
        or len(candidate_predictions) != len(documents)
        or set(champion_by_id) != expected_ids
        or set(candidate_by_id) != expected_ids
    ):
        raise ValueError("Predictions must contain each benchmark ID exactly once")

    review_items: list[ReviewItem] = []
    for document in documents:
        champion = champion_by_id[document.doc_id]
        candidate = candidate_by_id[document.doc_id]
        reasons = _review_reasons(document, candidate, policy)
        if reasons:
            review_items.append(
                ReviewItem(
                    document.doc_id,
                    document.segment,
                    document.text,
                    document.expected_topic,
                    document.expected_risk,
                    champion.predicted_topic,
                    candidate.predicted_topic,
                    champion.predicted_risk,
                    candidate.predicted_risk,
                    candidate.confidence,
                    reasons,
                )
            )

    champion_metrics = ModelMetrics(
        topic_accuracy=_accuracy(documents, champion_by_id, "expected_topic", "predicted_topic"),
        risk_accuracy=_accuracy(documents, champion_by_id, "expected_risk", "predicted_risk"),
        review_rate=0.0,
        invalid_label_count=_invalid_count(champion_predictions),
    )
    candidate_metrics = ModelMetrics(
        topic_accuracy=_accuracy(documents, candidate_by_id, "expected_topic", "predicted_topic"),
        risk_accuracy=_accuracy(documents, candidate_by_id, "expected_risk", "predicted_risk"),
        review_rate=len(review_items) / len(documents),
        invalid_label_count=_invalid_count(candidate_predictions),
    )

    by_segment: dict[str, list[Document]] = defaultdict(list)
    for document in documents:
        by_segment[document.segment].append(document)
    slice_metrics = [
        SliceMetrics(
            segment,
            len(segment_documents),
            _accuracy(segment_documents, champion_by_id, "expected_topic", "predicted_topic"),
            _accuracy(segment_documents, candidate_by_id, "expected_topic", "predicted_topic"),
            _accuracy(segment_documents, champion_by_id, "expected_risk", "predicted_risk"),
            _accuracy(segment_documents, candidate_by_id, "expected_risk", "predicted_risk"),
        )
        for segment, segment_documents in sorted(by_segment.items())
    ]
    critical = next(item for item in slice_metrics if item.segment == CRITICAL_SEGMENT)

    overall_regression = champion_metrics.topic_accuracy - candidate_metrics.topic_accuracy
    critical_regression = critical.champion_topic_accuracy - critical.candidate_topic_accuracy
    gates = [
        GateResult(
            "valid-labels",
            "Controlled labels",
            candidate_metrics.invalid_label_count == 0,
            str(candidate_metrics.invalid_label_count),
            "0 invalid labels",
            "Candidate outputs must stay inside the declared topic and risk taxonomies.",
        ),
        GateResult(
            "topic-accuracy",
            "Topic accuracy floor",
            candidate_metrics.topic_accuracy >= policy.min_topic_accuracy,
            f"{candidate_metrics.topic_accuracy:.1%}",
            f">= {policy.min_topic_accuracy:.1%}",
            "The candidate must meet the minimum benchmark accuracy.",
        ),
        GateResult(
            "risk-accuracy",
            "Risk accuracy floor",
            candidate_metrics.risk_accuracy >= policy.min_risk_accuracy,
            f"{candidate_metrics.risk_accuracy:.1%}",
            f">= {policy.min_risk_accuracy:.1%}",
            "Risk labels are evaluated separately from topic labels.",
        ),
        GateResult(
            "overall-regression",
            "No overall topic regression",
            overall_regression <= policy.max_overall_topic_regression,
            f"{overall_regression:+.1%}",
            f"<= {policy.max_overall_topic_regression:.1%}",
            "A positive value means the candidate is worse than the champion.",
        ),
        GateResult(
            "critical-slice",
            f"No {CRITICAL_SEGMENT} topic regression",
            critical_regression <= policy.max_critical_slice_topic_regression,
            f"{critical_regression:+.1%}",
            f"<= {policy.max_critical_slice_topic_regression:.1%}",
            "A protected slice cannot be hidden by a better aggregate score.",
        ),
        GateResult(
            "review-rate",
            "Review workload ceiling",
            candidate_metrics.review_rate <= policy.max_review_rate,
            f"{candidate_metrics.review_rate:.1%}",
            f"<= {policy.max_review_rate:.1%}",
            "The estimated review queue must remain operationally bounded.",
        ),
    ]
    decision = "PASS" if all(gate.passed for gate in gates) else "BLOCK"

    benchmark_payload = [asdict(document) for document in documents]
    benchmark_digest = hashlib.sha256(
        json.dumps(benchmark_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    policy_digest = hashlib.sha256(
        json.dumps(asdict(policy), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    serialized_review_items = serialize(review_items)
    evaluation_payload = {
        "scenario_id": scenario.scenario_id,
        "benchmark_digest": benchmark_digest,
        "policy_digest": policy_digest,
        "champion_version": champion_predictions[0].model_version,
        "candidate_version": candidate_predictions[0].model_version,
        "champion_artifact_digest": champion_artifact_digest,
        "candidate_artifact_digest": candidate_artifact_digest,
        "champion_metrics": serialize(champion_metrics),
        "candidate_metrics": serialize(candidate_metrics),
        "slice_metrics": serialize(slice_metrics),
        "gates": serialize(gates),
        "review_items": serialized_review_items,
    }
    evaluation_fingerprint = hashlib.sha256(
        json.dumps(evaluation_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return {
        **evaluation_payload,
        "evaluation_fingerprint": evaluation_fingerprint,
        "initial_decision": decision,
        "current_decision": decision,
        "decision_log": [],
    }
