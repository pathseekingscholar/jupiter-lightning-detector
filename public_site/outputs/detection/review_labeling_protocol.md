# Human Labeling Protocol

This protocol explains how to turn detector candidates into review evidence without making unsupported discovery claims.

## Current Review Set

- First-pass candidates: 106
- Required label file: `outputs/detection/candidate_label_template.csv`
- Import command after review: `.\run.ps1 label-import -LabelCsv outputs\detection\candidate_label_template.csv`
- Regenerate summaries after import: `.\run.ps1 label-summary`

## Reviewer Rule

A detector candidate is not lightning by itself. A label records what the reviewer thinks the candidate is, and the note explains why.

## Label Definitions

| Label | Use when | Do not use when | Training role |
|---|---|---|---|
| `known-lightning` | Candidate matches a published Dyudina et al. validation mark and the reviewer visually confirms the mark. | The row is merely near a published image but not the validation mark. | Positive validation example. |
| `possible-lightning` | Diffuse bright blob or repeated candidate that remains scientifically interesting after artifact checks. | Only one sharp pixel, streak, edge effect, or no temporal/geometric support. | Candidate positive only after second review; not a confirmed discovery. |
| `artifact` | Likely edge, streak, processing residual, line defect, saturated artifact, or shape inconsistent with lightning. | The candidate is diffuse and repeated enough to need more review. | Negative example. |
| `cosmic-ray-hot-pixel` | Single-pixel or very sharp point-like event that disappears in nearby frames. | Multi-pixel diffuse blob with repeat behavior. | Negative example. |
| `uncertain` | Evidence is mixed, too faint, too ambiguous, or needs another frame/filter/geometry check. | A clear positive validation mark or clear artifact can be labeled directly. | Holdout; not used for first training pass. |

## Required Fields

| Field | Meaning |
|---|---|
| `human_label` | One of the allowed labels above. |
| `confidence` | Reviewer confidence: `low`, `medium`, or `high`. |
| `reviewer` | Name or initials of the person reviewing. |
| `review_note` | Short reason for the label; do not leave this blank for training rows. |
| `review_stage` | `first-review`, `second-review`, or `consensus`. |
| `needs_second_review` | `yes` when the row should not be used alone. |
| `reviewed_at` | Review timestamp; the importer can fill this if blank. |

## Batch Checklist

| Batch | Count | Goal | Preferred labels | Pass condition |
|---|---:|---|---|---|
| `01_known_validation_positive` | 6 | Confirm published validation marks after visual inspection. | known-lightning or uncertain | All six published matches have reviewer, confidence, note, and reviewed_at. |
| `02_temporal_persistence_check` | 30 | Check whether candidate tracks persist across nearby frames. | possible-lightning, artifact, cosmic-ray-hot-pixel, or uncertain | Every strong temporal case has a note about repeat behavior. |
| `03_negative_artifact_examples` | 20 | Build negative examples for false-positive analysis. | artifact or cosmic-ray-hot-pixel | At least 20 clear negative labels with short reason notes. |
| `04_strong_single_frame_check` | 20 | Inspect strong one-frame detections without overclaiming them. | possible-lightning, artifact, cosmic-ray-hot-pixel, or uncertain | Each row notes why single-frame evidence is or is not credible. |
| `05_low_priority_hold` | 30 | Keep lower-priority examples available without using them too early. | uncertain, artifact, or hold unlabeled | No discovery claim comes from this batch alone. |

## Positive / Negative Meaning

- Positive examples are `known-lightning` or carefully reviewed `possible-lightning` rows.
- Negative examples are `artifact` or `cosmic-ray-hot-pixel` rows.
- `uncertain` rows stay out of training until more evidence exists.
- Published validation marks should be labeled before any unmatched candidate is presented as interesting.

## Minimum First Review Target

- 6 known validation positives.
- 20 clear negative artifact or cosmic-ray/hot-pixel examples.
- Notes for every temporal candidate that might become `possible-lightning`.

## What This Enables

Once labels exist, the project can report false positives, false negatives, training-ready examples, and reviewer disagreement. Only after that should YOLO or another learned model be compared against the explainable detector.