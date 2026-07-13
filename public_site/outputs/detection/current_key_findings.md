# Current Key Findings

This is a generated brief. It pulls numbers from the current detector outputs so the meeting summary and GitHub evidence stay tied to the same files.

## Two-Minute Bottom Line

- The pipeline has processed nine Cassini ISS NAC/H-alpha date windows around the Jupiter flyby.
- The current search scope is 221 images.
- The detector recovers the six published validation marks across Jan 1, Jan 10, and Jan 11.
- The detector also keeps unmatched review candidates, but those are not new-lightning claims.
- The next scientific gate is human yes/no/uncertain labeling, followed by temporal and geometry checks.

## Key Numbers

| Item | Value | Evidence | Interpretation |
|---|---:|---|---|
| `processed_date_windows` | 9 | `outputs/detection/detection_summary.csv` | Nine OPUS NAC/H-alpha date windows are currently processed. |
| `images_processed` | 221 | `outputs/detection/detection_summary.csv` | This is the current image-level search scope. |
| `raw_bright_regions` | 196,233 | `outputs/detection/detection_summary.csv` | First-pass bright regions before review filtering. |
| `review_candidates` | 12,611 | `outputs/detection/detection_summary.csv` | Candidates kept after artifact filters; these are not confirmed lightning. |
| `rejected_or_artifact_flagged` | 183,622 | `outputs/detection/detection_summary.csv` | Bright regions the detector deprioritized or flagged as likely artifact-like. |
| `published_validation_matches` | 6 detector matches; 6 recovered within 8 px | `outputs/detection/known_match_report.csv` | The current detector recovers the published validation marks. |
| `unmatched_review_candidates` | 12,605 | `outputs/detection/detection_summary.csv` | Unmatched means not in the published answer key; it does not mean new lightning. |
| `first_pass_review_rows` | 106 | `outputs/detection/first_pass_review_plan.csv` | Curated queue for human yes/no/uncertain review. |
| `review_sessions` | 10 sessions; 0 import-ready | `outputs/detection/review_session_audit.csv` | Session CSVs organize human review work; labels still need to be filled. |
| `training_readiness` | saved_labels_exist: not_ready; positive_examples: not_ready; negative_examples: not_ready; training_ready_labels: not_ready | `outputs/detection/training_readiness.csv` | Learned-model work is gated on enough reviewed labels. |

## Date Coverage

| Date | Images | Raw regions | Review candidates | Published matches | Unmatched review |
|---|---:|---:|---:|---:|---:|
| 2000-12-31 | 12 | 5,035 | 565 | 0 | 565 |
| 2001-01-01 | 23 | 9,447 | 1,094 | 2 | 1,092 |
| 2001-01-04 | 17 | 3,888 | 483 | 0 | 483 |
| 2001-01-05 | 22 | 4,784 | 573 | 0 | 573 |
| 2001-01-08 | 54 | 115,644 | 6,310 | 0 | 6,310 |
| 2001-01-09 | 11 | 7,491 | 370 | 0 | 370 |
| 2001-01-10 | 26 | 5,880 | 472 | 2 | 470 |
| 2001-01-11 | 31 | 6,737 | 418 | 2 | 416 |
| 2001-01-13 | 25 | 37,327 | 2,326 | 0 | 2,326 |

## Published-Match Validation

| Image | Published mark | Paper x/y | Detector x/y | Offset px | Recovered? |
|---|---|---:|---:|---:|---|
| N1357029177 | 1 | 731.0, 211.0 | 731.37, 212.49 | 1.54 | yes |
| N1357029177 | 2 | 846.0, 397.0 | 847.00, 402.23 | 5.32 | yes |
| N1357810970 | 3 | 955.0, 357.0 | 955.53, 354.96 | 2.11 | yes |
| N1357810970 | 3* | 951.0, 330.0 | 951.80, 333.08 | 3.18 | yes |
| N1357885387 | 4 | 775.0, 341.0 | 769.65, 339.50 | 5.56 | yes |
| N1357885387 | 4* | 775.0, 316.0 | 776.00, 318.00 | 2.24 | yes |

## Human Review Queue

| Review batch | Rows | What a human does |
|---|---:|---|
| 01_known_validation_positive | 6 | Confirm that published matches are visually reasonable. |
| 02_temporal_persistence_check | 30 | Check whether repeated candidates look like coherent motion or repeated artifacts. |
| 03_negative_artifact_examples | 20 | Build a clean negative set for cosmic rays, hot pixels, and artifacts. |
| 04_strong_single_frame_check | 20 | Inspect strong one-frame signals without overclaiming them. |
| 05_low_priority_hold | 30 | Keep low-priority rows saved but not first in the review queue. |

## What We Can Safely Say

- I built a reproducible detector-and-review workflow for Cassini Jupiter lightning candidates.
- The detector recovers the published validation marks in the current processed dataset.
- The detector produces a saved review queue with positives, likely negatives, temporal candidates, and unmatched candidates.
- The work is ready for structured human review, not for claiming new lightning yet.

## What We Cannot Say Yet

- We cannot say the unmatched candidates are confirmed new Jupiter lightning.
- We cannot say the candidate score is a calibrated probability.
- We cannot say YOLO or a trained model is ready; labels are still needed.
- We cannot claim Jupiter latitude/longitude for candidate pixels until geometry projection is completed.

## Open First

- `outputs/detection/candidate_review_dossier.html` for reviewer-facing candidates.
- `outputs/detection/known_match_report.csv` for published validation recovery.
- `outputs/detection/first_pass_review_plan.md` for the ordered human review plan.
- `outputs/detection/temporal_validation_plan.md` for repeated-track follow-up.
- `outputs/detection/manuscript_claim_matrix.md` for safe/unsafe paper wording.