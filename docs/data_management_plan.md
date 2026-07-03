# Data Management Plan

## Principle

Keep raw archive data reproducible, generated review outputs traceable, and
scientific claims conservative.

## What Stays In Git

- Source code.
- Small documentation files.
- JSON schemas.
- Known published validation marks.
- Reproducibility instructions.
- Lightweight issue templates and roadmap files.

## What Stays Out Of Git

- Raw calibrated image products.
- Preview images downloaded from OPUS.
- Large generated contact sheets.
- Generated CSV outputs when they are large or easy to reproduce.
- Local browser labels that may change during review.

## Local Generated Output Directory

The main generated directory is:

```text
outputs/detection
```

The important reproducible files are:

- `detection_summary.csv`
- `dataset_manifest.csv`
- `known_match_report.csv`
- `temporal_track_summary.csv`
- `scientific_review_queue.csv`
- `training_manifest.csv`
- `active_learning_queue.csv`
- `review_packet.md`

## Human Review Records

Human labels should record:

- candidate ID,
- image ID,
- label,
- reviewer,
- review time,
- confidence,
- short note,
- whether a second review is needed.

The schema is stored at `schemas/candidate_label.schema.json`.

## Publication Boundary

Generated candidates may be used in internal review and method development.
Only candidates that survive manual review and temporal/geometric validation
should be described as scientific detections.
