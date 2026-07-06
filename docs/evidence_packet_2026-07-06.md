# Evidence Packet - 2026-07-06

This packet summarizes the current state of the Cassini Jupiter lightning
detector in plain research terms. It is written as a status checkpoint, not as a
discovery claim.

## One-Sentence Status

I have a reproducible, explainable detector-and-review workflow that recovers
the six published validation marks and turns the larger Cassini output into a
curated human-review queue. I do not yet have human-confirmed new lightning.

## What Is Proven Right Now

- The detector pipeline runs across the current Cassini Jupiter date windows.
- The generated outputs report 221 processed images.
- The pipeline saves all first-pass bright regions instead of hiding them.
- The detector recovered six published validation matches in the current output
  tables.
- The workflow now separates detector output from human review labels.
- The repo has tests and an output validator for generated research artifacts.

## What Is Not Proven Yet

- The unmatched candidates are not confirmed lightning.
- The candidate score is a review priority, not a true lightning probability.
- YOLO or another learned detector has not been trained yet.
- The current human-label file has zero reviewed labels inside the current
  106-row manifest.
- Color or spectrum behavior is not proven by nearby filter context alone.

## Current Numbers

These numbers come from the generated files in `outputs/detection`.

| Quantity | Value |
|---|---:|
| Images processed | 221 |
| Raw bright regions found | 196,233 |
| Review candidates after artifact filters | 12,611 |
| Published validation matches recovered | 6 |
| Unmatched review candidates | 12,605 |
| Curated first-pass review rows | 106 |
| Human labels saved in current manifest | 0 |

The high raw candidate count is expected. Jupiter night-side images contain
noise, hot pixels, cosmic-ray-like features, edges, and small bright regions.
The detector is intentionally broad at first so potential signals are not thrown
away before review.

## First-Pass Review Plan

The first review pass keeps all 106 curated candidates accounted for.

| Review batch | Rows | Purpose |
|---|---:|---|
| Known validation positives | 6 | Confirm published matches as positive examples. |
| Temporal persistence check | 30 | Check repeated candidates across nearby frames. |
| Negative artifact examples | 20 | Label clear artifacts/hot pixels for false-positive analysis. |
| Strong single-frame check | 20 | Inspect high-SNR candidates cautiously. |
| Low-priority hold | 30 | Preserve remaining candidates for later review. |

The key file is `outputs/detection/first_pass_review_plan.csv`.

## Positive, Negative, And Uncertain Labels

- Positive means a human labels a row as `known-lightning` or
  `possible-lightning`.
- Negative means a human labels a row as `artifact` or
  `cosmic-ray-hot-pixel`.
- Uncertain means the row is worth follow-up but is not clean training data yet.
- Unlabeled means detector output only; it is not scientific confirmation.

The current audit says:

| Audit item | Current value |
|---|---:|
| Candidate rows available for review | 106 |
| Positive training examples | 0 |
| Negative training examples | 0 |
| Unlabeled candidates remaining | 106 |
| Published validation marks human-labeled positive | 0 of 6 |

The key file is `outputs/detection/human_review_audit.md`.

## Nearby Filter Context

The new filter-context audit searches OPUS for non-H-alpha Cassini ISS NAC
images within +/- 20 minutes of review candidates.

| Nearby filter | Context rows |
|---|---:|
| BL1 | 120 |
| BL2 | 56 |
| CB2 | 154 |
| GRN | 56 |
| MT2 | 107 |
| MT3 | 107 |
| RED | 56 |
| UV3 | 113 |

This is useful for follow-up. It does not prove lightning color or spectrum by
itself.

## What To Show In A Meeting

1. Open the workbench and show the detector/review links.
2. Open `human_review_audit.md` to explain positives, negatives, and unlabeled
   candidates.
3. Open `first_pass_review_plan.md` to show exactly what a human should label
   first.
4. Open `nearby_filter_context_report.md` to show the follow-up path toward
   color/spectrum context.
5. State the safe claim clearly: this is a validated candidate-generation and
   review workflow, not confirmed new lightning yet.

## Recent Git Checkpoints

- `746e4ab` - Added nearby filter context audit.
- `e8ee51a` - Added human review/training audit.
- `69eb240` - Added first-pass review labeling plan.

## Next Scientific Gate

The next real scientific step is not a prettier UI and not YOLO. It is the first
human review pass:

1. Label the six known validation positives.
2. Label at least 20 clear negative artifact examples.
3. Review temporal candidates for persistence across frames.
4. Re-run the audit and check whether enough positives/negatives exist for a
   small baseline model comparison.
5. Only then compare YOLO or another learned detector against the explainable
   baseline.
