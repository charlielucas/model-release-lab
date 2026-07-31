"""Deterministic synthetic training and benchmark records."""

from __future__ import annotations

from .domain import Document


def _documents(prefix: str, rows: list[tuple[str, str, str]]) -> list[Document]:
    return [
        Document(
            doc_id=f"{prefix}-{index:03d}",
            text=text,
            expected_topic=topic,
            expected_risk=risk,
            segment=topic,
        )
        for index, (text, topic, risk) in enumerate(rows, start=1)
    ]


TRAINING_DOCUMENTS = _documents(
    "TRN",
    [
        ("Customer requests a refund after a damaged delivery", "Customer Support", "Medium"),
        ("Billing support needs to correct an account charge", "Customer Support", "Low"),
        (
            "Login reset failed and the customer cannot access the account",
            "Customer Support",
            "High",
        ),
        ("Support escalation reports a delayed replacement shipment", "Customer Support", "Medium"),
        ("Customer asks how to update a subscription", "Customer Support", "Low"),
        ("Refund was sent to the wrong account owner", "Customer Support", "High"),
        ("Revenue forecast changed after a delayed vendor invoice", "Finance", "Medium"),
        ("Finance team completed the monthly close checklist", "Finance", "Low"),
        ("An approval error could create a material reporting issue", "Finance", "High"),
        ("The invoice reconciliation found a duplicate payment", "Finance", "Medium"),
        ("Quarterly budget variance is within the expected range", "Finance", "Low"),
        ("A payment file exposed confidential banking fields", "Finance", "High"),
        ("Security review found an exposed authentication token", "Security", "High"),
        ("Access logs show repeated failed authorization attempts", "Security", "Medium"),
        ("Routine vulnerability scan found no exploitable issue", "Security", "Low"),
        ("A critical dependency flaw permits unauthorized access", "Security", "High"),
        ("Credential rotation completed after a staging incident", "Security", "Medium"),
        ("The test environment passed its access-control review", "Security", "Low"),
        ("Product feedback asks for clearer export controls", "Product Feedback", "Low"),
        ("User interview reports a confusing onboarding flow", "Product Feedback", "Medium"),
        ("A missing empty state could hide a destructive action", "Product Feedback", "High"),
        ("Customers requested saved filters in the dashboard", "Product Feedback", "Low"),
        ("Usability testing found unclear navigation labels", "Product Feedback", "Medium"),
        ("Feedback warns that the delete control lacks confirmation", "Product Feedback", "High"),
    ],
)


BENCHMARK_DOCUMENTS = _documents(
    "BEN",
    [
        ("A shopper needs help reversing a damaged-item charge", "Customer Support", "Medium"),
        (
            "The help desk cannot restore access after repeated reset attempts",
            "Customer Support",
            "High",
        ),
        ("A subscriber asks for a copy of the latest receipt", "Customer Support", "Low"),
        ("An escalation says a replacement has not arrived", "Customer Support", "Medium"),
        ("The service team resolved a routine profile update", "Customer Support", "Low"),
        ("Month-end reconciliation found two copies of one invoice", "Finance", "Medium"),
        ("The controller approved an ordinary forecast update", "Finance", "Low"),
        ("A reporting file included confidential payment details", "Finance", "High"),
        ("The budget review found a material revenue mismatch", "Finance", "High"),
        ("Vendor payment timing moved by one business day", "Finance", "Low"),
        ("An authorization bypass exposed a temporary credential", "Security", "High"),
        ("The access review found several unexpected login attempts", "Security", "Medium"),
        ("A routine scan confirmed the patch removed the flaw", "Security", "Low"),
        ("Credential rotation followed a suspicious test event", "Security", "Medium"),
        ("No customer information was reached during the security test", "Security", "Low"),
        ("Research participants want a clearer first-run experience", "Product Feedback", "Medium"),
        ("People requested a reusable view for common filters", "Product Feedback", "Low"),
        ("The interface can erase a draft without confirmation", "Product Feedback", "High"),
        ("A usability session found the navigation wording unclear", "Product Feedback", "Medium"),
        ("The empty screen now explains how to add the first item", "Product Feedback", "Low"),
    ],
)
