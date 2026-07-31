"""Guided public scenarios and release policy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleasePolicy:
    min_topic_accuracy: float = 0.60
    min_risk_accuracy: float = 0.70
    max_overall_topic_regression: float = 0.0
    max_critical_slice_topic_regression: float = 0.0
    max_review_rate: float = 0.55
    review_confidence_threshold: float = 0.42


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    name: str
    question: str
    description: str
    failure_fixture: str
    expected_decision: str


SCENARIOS = (
    Scenario(
        "clean-release",
        "Clean release",
        "Can the candidate replace the current model without weakening a protected slice?",
        "The trained candidate is evaluated without injected failures.",
        "none",
        "PASS",
    ),
    Scenario(
        "critical-slice-regression",
        "Aggregate pass, critical slice failure",
        "What happens when overall results look acceptable but Security records regress?",
        "A versioned fixture changes only candidate predictions in the protected Security slice.",
        "critical-slice-regression",
        "BLOCK",
    ),
    Scenario(
        "schema-violation",
        "Unknown label",
        "Will a candidate be blocked when it emits a label outside the controlled taxonomy?",
        "One candidate output is replaced with an unmapped topic label.",
        "schema-violation",
        "BLOCK",
    ),
    Scenario(
        "review-surge",
        "Review workload surge",
        "Will a release stop when confidence drift sends too many records to review?",
        "Candidate confidence is reduced while its labels remain unchanged.",
        "review-surge",
        "BLOCK",
    ),
    Scenario(
        "override-and-rollback",
        "Override and rollback",
        "Can a blocked run record a reviewer override and a later rollback?",
        "The critical-slice regression is used to exercise the bounded decision log.",
        "override-and-rollback",
        "BLOCK",
    ),
)


SCENARIO_BY_ID = {scenario.scenario_id: scenario for scenario in SCENARIOS}
