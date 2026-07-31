"""Core domain types for model evaluation runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

TOPIC_LABELS = ("Customer Support", "Finance", "Security", "Product Feedback")
RISK_LABELS = ("Low", "Medium", "High")
CRITICAL_SEGMENT = "Security"


@dataclass(frozen=True)
class Document:
    doc_id: str
    text: str
    expected_topic: str
    expected_risk: str
    segment: str


@dataclass(frozen=True)
class Prediction:
    doc_id: str
    predicted_topic: str
    predicted_risk: str
    confidence: float
    model_version: str


@dataclass(frozen=True)
class ModelMetrics:
    topic_accuracy: float
    risk_accuracy: float
    review_rate: float
    invalid_label_count: int


@dataclass(frozen=True)
class SliceMetrics:
    segment: str
    count: int
    champion_topic_accuracy: float
    candidate_topic_accuracy: float
    champion_risk_accuracy: float
    candidate_risk_accuracy: float


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    label: str
    passed: bool
    measured: str
    threshold: str
    reason: str


@dataclass(frozen=True)
class ReviewItem:
    doc_id: str
    segment: str
    text: str
    expected_topic: str
    expected_risk: str
    champion_topic: str
    candidate_topic: str
    champion_risk: str
    candidate_risk: str
    candidate_confidence: float
    reasons: tuple[str, ...]


def serialize(value: Any) -> Any:
    """Convert nested dataclasses and tuples into JSON-safe values."""

    if hasattr(value, "__dataclass_fields__"):
        return {key: serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(item) for item in value]
    return value
