"""Transparent document labeler."""

from __future__ import annotations


TOPIC_KEYWORDS = {
    "Customer Support": ["refund", "support", "account", "billing", "customer"],
    "Finance": ["finance", "revenue", "vendor", "invoice", "close"],
    "Security": ["security", "token", "auth", "vulnerability", "accessed"],
    "Product Feedback": ["feedback", "filters", "export", "onboarding", "empty state"],
}

HIGH_RISK_TERMS = ["critical", "vulnerability", "exposed", "access issue"]
MEDIUM_RISK_TERMS = ["damaged", "delayed", "approved", "wrong account", "accessed"]


def label_topic(text: str) -> str:
    lowered = text.lower()
    scores = {
        topic: sum(1 for keyword in keywords if keyword in lowered)
        for topic, keywords in TOPIC_KEYWORDS.items()
    }
    return max(scores, key=scores.get)


def label_risk(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in HIGH_RISK_TERMS):
        return "High"
    if any(term in lowered for term in MEDIUM_RISK_TERMS):
        return "Medium"
    return "Low"


def label_documents(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    labeled: list[dict[str, object]] = []
    for row in rows:
        predicted_topic = label_topic(row["text"])
        predicted_risk = label_risk(row["text"])
        labeled.append(
            {
                **row,
                "predicted_topic": predicted_topic,
                "predicted_risk": predicted_risk,
                "topic_match": str(predicted_topic == row["expected_topic"]),
                "risk_match": str(predicted_risk == row["expected_risk"]),
            }
        )
    return labeled
