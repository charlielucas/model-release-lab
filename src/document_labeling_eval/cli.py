"""Command line entry points for the document labeling workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from .evaluator import accuracy, missed_rows
from .io import read_csv, write_csv
from .labeler import label_documents


ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_PATH = ROOT / "data" / "documents.csv"
LABELED_PATH = ROOT / "examples" / "labeled_documents.csv"
REPORT_PATH = ROOT / "examples" / "evaluation_report.md"


def label(input_path: Path = DOCUMENTS_PATH, output_path: Path = LABELED_PATH) -> list[dict[str, object]]:
    rows = read_csv(input_path)
    labeled = label_documents(rows)
    fieldnames = list(labeled[0].keys()) if labeled else []
    write_csv(output_path, labeled, fieldnames)
    return labeled


def evaluate(labeled_path: Path = LABELED_PATH, output_path: Path = REPORT_PATH) -> str:
    rows = read_csv(labeled_path)
    misses = missed_rows(rows)
    lines = [
        "# Evaluation Report",
        "",
        f"- Documents: {len(rows)}",
        f"- Topic accuracy: {accuracy(rows, 'topic_match'):.1%}",
        f"- Risk accuracy: {accuracy(rows, 'risk_match'):.1%}",
        f"- Rows needing review: {len(misses)}",
        "",
        "## Rows Needing Review",
        "",
        "| doc | expected topic | predicted topic | expected risk | predicted risk |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in misses:
        lines.append(
            "| {doc_id} | {expected_topic} | {predicted_topic} | {expected_risk} | {predicted_risk} |".format(
                **row
            )
        )
    lines.append("")

    output = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Document labeling evaluation workflow")
    parser.add_argument("command", choices=["label", "evaluate"])
    parser.add_argument("--documents-path", type=Path, default=DOCUMENTS_PATH)
    parser.add_argument("--labeled-path", type=Path, default=LABELED_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    if args.command == "label":
        rows = label(input_path=args.documents_path, output_path=args.labeled_path)
        print(f"Wrote {len(rows)} labeled rows to {args.labeled_path}")
    elif args.command == "evaluate":
        print(evaluate(labeled_path=args.labeled_path, output_path=args.report_path))


if __name__ == "__main__":
    main()
