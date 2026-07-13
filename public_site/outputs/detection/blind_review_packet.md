# Single-Blind Review Packet

This packet lets a reviewer label candidates without seeing the detector's suggested label, review batch, or next action. It is single-blind, not double-blind: the candidate image/crop, coordinates, and measured detector numbers are still visible.

## Files

- Reviewer file: `outputs/detection/blind_review_packet.csv`
- Answer key: `outputs/detection/blind_review_key.csv`

## Review Rules

- Do not open the answer key until the first-pass blind labels are finished.
- Use `reviewer_label` values from the normal label set: `known-lightning`, `possible-lightning`, `artifact`, `cosmic-ray-hot-pixel`, or `uncertain`.
- Use `reviewer_confidence`: `low`, `medium`, or `high`.
- Write a short `reviewer_note` explaining the visual reason for the label.
- Set `needs_second_review` to `yes` for ambiguous rows.

## Packet Summary

- Blind rows: 106
- Answer-key rows: 106

| Hidden review batch | Rows |
|---|---:|
| `01_known_validation_positive` | 6 |
| `02_temporal_persistence_check` | 30 |
| `03_negative_artifact_examples` | 20 |
| `04_strong_single_frame_check` | 20 |
| `05_low_priority_hold` | 30 |

## Why This Exists

The normal review plan is efficient because it tells the reviewer which rows are published matches, likely artifacts, or temporal candidates. The blind packet is slower but less biased. It is useful when the project needs a cleaner estimate of human agreement, false positives, and whether detector categories are visually convincing.

## After Review

Join `blind_review_packet.csv` to `blind_review_key.csv` by `blind_id`, then compare reviewer labels against the hidden suggested labels and batches. Do not treat disagreement as failure automatically; disagreement is evidence that the candidate needs clearer criteria or second review.