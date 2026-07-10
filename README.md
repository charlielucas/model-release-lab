# Document Labeling Evaluation

A small Python project for labeling short synthetic documents and checking the results against expected labels.

The data is synthetic. It is not employer data, customer data, medical data, or legal data.

## What It Does

The workflow reads short document snippets, assigns a topic and risk label, and writes an evaluation report.

It is meant to show a practical pattern used around LLM and NLP work:

- define an expected label set
- label documents in a repeatable way
- keep predicted and expected labels side by side
- report accuracy by field
- list misses for review

There are no API calls in this repo. The labeler is deliberately transparent so the evaluation flow is easy to inspect.

## Quick Start

Use Python 3.9 or newer.

```bash
PYTHONPATH=src python3 -m document_labeling_eval label
PYTHONPATH=src python3 -m document_labeling_eval evaluate
```

Or use the Makefile:

```bash
make test
make demo
```

## Outputs

- `examples/labeled_documents.csv`
- `examples/evaluation_report.md`

## Design Notes

This is a small version of a document labeling workflow. A larger version could swap in embeddings or an LLM, but the evaluation shape would stay similar: define labels, capture predictions, compare results, and inspect errors.

## Known Limits

- The documents are synthetic.
- The labeler is keyword based.
- The label set is small.
- The report is text-based by design.

