# First-Pass Review Plan

This is the practical labeling order for turning detector candidates into human-reviewed evidence. It is intentionally small enough to start in a meeting or lab session.

## Review Order

1. Confirm the six known published lightning matches as positive validation examples.
2. Review temporal candidates that repeat across frames.
3. Label clear artifacts and cosmic-ray/hot-pixel examples as negatives.
4. Inspect strong single-frame candidates, but do not overclaim them.

## Batch Counts

| Batch | Rows | Purpose |
|---|---:|---|
| `01_known_validation_positive` | 6 | Confirm known positive validation examples. |
| `02_temporal_persistence_check` | 30 | Search for repeated candidates across frames. |
| `03_negative_artifact_examples` | 20 | Build negative examples for false-positive analysis. |
| `04_strong_single_frame_check` | 20 | Review high-SNR single-frame candidates cautiously. |
| `05_low_priority_hold` | 30 | Keep the rest without deleting them. |

## Labeling Rule

A row becomes training data only after a human fills in a label, confidence, reviewer name, and note. The detector suggestion is not the final truth.

## Meeting-Friendly Explanation

I am not training YOLO yet. I am building the labeled evidence set first: positives, negatives, uncertain cases, and temporal-review candidates. Once those labels exist, a learned model can be tested against this baseline.