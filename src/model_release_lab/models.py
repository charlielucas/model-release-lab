"""Transparent and scikit-learn prediction adapters."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict
from typing import Protocol

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .domain import Document, Prediction


class PredictionModel(Protocol):
    version: str
    artifact_digest: str

    def predict(self, documents: Iterable[Document]) -> list[Prediction]: ...


class RulesModel:
    """Small, inspectable champion that intentionally has known vocabulary gaps."""

    version = "rules-champion-1.0"
    topic_keywords = {
        "Customer Support": ("customer", "support", "refund", "account", "billing"),
        "Finance": ("finance", "revenue", "vendor", "invoice", "budget"),
        "Security": ("security", "token", "auth", "vulnerability", "access"),
        "Product Feedback": ("feedback", "filters", "onboarding", "navigation", "empty"),
    }
    high_risk_terms = ("critical", "exposed", "bypass", "material")
    medium_risk_terms = ("damaged", "delayed", "duplicate", "unexpected", "confusing")

    def __init__(self) -> None:
        model_spec = {
            "topic_keywords": self.topic_keywords,
            "high_risk_terms": self.high_risk_terms,
            "medium_risk_terms": self.medium_risk_terms,
        }
        self.artifact_digest = hashlib.sha256(
            json.dumps(model_spec, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def predict(self, documents: Iterable[Document]) -> list[Prediction]:
        predictions: list[Prediction] = []
        for document in documents:
            lowered = document.text.lower()
            scores = {
                topic: sum(keyword in lowered for keyword in keywords)
                for topic, keywords in self.topic_keywords.items()
            }
            topic = max(scores, key=scores.get)
            if any(term in lowered for term in self.high_risk_terms):
                risk = "High"
            elif any(term in lowered for term in self.medium_risk_terms):
                risk = "Medium"
            else:
                risk = "Low"
            best_score = scores[topic]
            confidence = min(0.94, 0.55 + 0.13 * best_score)
            predictions.append(Prediction(document.doc_id, topic, risk, confidence, self.version))
        return predictions


class SklearnTextModel:
    """Deterministic TF-IDF and logistic-regression candidate."""

    vectorizer_config = {
        "ngram_range": (1, 2),
        "min_df": 1,
        "sublinear_tf": True,
    }
    classifier_config = {"max_iter": 500, "random_state": 17, "C": 30}

    def __init__(self, training_documents: Iterable[Document]) -> None:
        training = list(training_documents)
        training_payload = [asdict(document) for document in training]
        self.training_digest = hashlib.sha256(
            json.dumps(training_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        artifact_spec = {
            "training_digest": self.training_digest,
            "vectorizer": self.vectorizer_config,
            "classifier": self.classifier_config,
        }
        self.artifact_digest = hashlib.sha256(
            json.dumps(artifact_spec, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.version = f"tfidf-logreg-candidate-2.0+{self.artifact_digest[:12]}"
        texts = [document.text for document in training]
        self.topic_pipeline = self._pipeline()
        self.risk_pipeline = self._pipeline()
        self.topic_pipeline.fit(texts, [document.expected_topic for document in training])
        self.risk_pipeline.fit(texts, [document.expected_risk for document in training])

    @staticmethod
    def _pipeline() -> Pipeline:
        return Pipeline(
            [
                ("tfidf", TfidfVectorizer(**SklearnTextModel.vectorizer_config)),
                (
                    "classifier",
                    LogisticRegression(**SklearnTextModel.classifier_config),
                ),
            ]
        )

    def predict(self, documents: Iterable[Document]) -> list[Prediction]:
        records = list(documents)
        texts = [document.text for document in records]
        topic_labels = self.topic_pipeline.predict(texts)
        risk_labels = self.risk_pipeline.predict(texts)
        topic_probabilities = self.topic_pipeline.predict_proba(texts)
        risk_probabilities = self.risk_pipeline.predict_proba(texts)
        return [
            Prediction(
                doc_id=document.doc_id,
                predicted_topic=str(topic),
                predicted_risk=str(risk),
                confidence=round(
                    (float(topic_probs.max()) + float(risk_probs.max())) / 2,
                    4,
                ),
                model_version=self.version,
            )
            for document, topic, risk, topic_probs, risk_probs in zip(
                records,
                topic_labels,
                risk_labels,
                topic_probabilities,
                risk_probabilities,
                strict=True,
            )
        ]


def apply_failure_fixture(
    predictions: list[Prediction],
    documents: list[Document],
    fixture: str,
) -> list[Prediction]:
    """Apply a versioned synthetic failure fixture to candidate outputs."""

    fixture_suffixes = {
        "none": "",
        "critical-slice-regression": "+security-regression-fixture-v1",
        "schema-violation": "+schema-violation-fixture-v1",
        "review-surge": "+confidence-drift-fixture-v1",
        "override-and-rollback": "+security-regression-fixture-v1",
    }
    if fixture not in fixture_suffixes:
        raise ValueError(f"Unknown failure fixture: {fixture}")

    document_by_id = {document.doc_id: document for document in documents}
    adjusted: list[Prediction] = []
    security_fixture_count = 0
    for index, prediction in enumerate(predictions):
        document = document_by_id[prediction.doc_id]
        topic = prediction.predicted_topic
        risk = prediction.predicted_risk
        confidence = prediction.confidence
        version = prediction.model_version + fixture_suffixes[fixture]

        if fixture in {"critical-slice-regression", "override-and-rollback"}:
            if document.segment == "Security" and security_fixture_count < 3:
                topic = "Finance"
                confidence = max(confidence, 0.82)
                security_fixture_count += 1
        elif fixture == "schema-violation" and index == 0:
            topic = "Unmapped"
            confidence = 0.91
        elif fixture == "review-surge":
            confidence = min(confidence, 0.30)

        adjusted.append(Prediction(prediction.doc_id, topic, risk, confidence, version))
    return adjusted
