# Review Session Plan

This turns the first-pass review queue into small CSV packets that a reviewer can label in one sitting. It is a workflow artifact, not a discovery catalog.

## How To Use

1. Open the next session CSV in `outputs/detection/review_sessions/`.
2. Inspect each crop and original context in the workbench.
3. Fill `human_label`, `confidence`, `reviewer`, `review_note`, `needs_second_review`, and optionally `reviewed_at`.
4. Import the completed CSV with `.\run.ps1 label-import -LabelCsv outputs\detection\review_sessions\SESSION_FILE.csv`.
5. Regenerate label summaries with `.\run.ps1 label-summary`, then rerun `.\run.ps1 training-readiness`.

## Summary

- Review sessions: 10
- Candidates assigned to sessions: 106

| Batch | Sessions | Purpose |
|---|---:|---|
| `01_known_validation_positive` | 1 | Confirm the published validation matches first. |
| `02_temporal_persistence_check` | 3 | Decide whether repeated candidates look physically plausible across frames. |
| `03_negative_artifact_examples` | 2 | Collect clear artifact and cosmic-ray/hot-pixel negatives. |
| `04_strong_single_frame_check` | 2 | Inspect strong one-frame detections without calling them discoveries. |
| `05_low_priority_hold` | 2 | Preserve lower-priority rows for later review. |

## Sessions

| Session | Rows | CSV | Allowed labels | Pass condition |
|---|---:|---|---|---|
| `S001_01_known_validation_positive` | 6 | `review_sessions/S001_01_known_validation_positive.csv` | known-lightning, uncertain | Every row has reviewer, confidence, note, and visual confirmation or uncertainty reason. |
| `S002_02_temporal_persistence_check` | 10 | `review_sessions/S002_02_temporal_persistence_check.csv` | possible-lightning, artifact, cosmic-ray-hot-pixel, uncertain | Every note mentions repeat behavior, motion, or why temporal evidence is weak. |
| `S003_02_temporal_persistence_check` | 10 | `review_sessions/S003_02_temporal_persistence_check.csv` | possible-lightning, artifact, cosmic-ray-hot-pixel, uncertain | Every note mentions repeat behavior, motion, or why temporal evidence is weak. |
| `S004_02_temporal_persistence_check` | 10 | `review_sessions/S004_02_temporal_persistence_check.csv` | possible-lightning, artifact, cosmic-ray-hot-pixel, uncertain | Every note mentions repeat behavior, motion, or why temporal evidence is weak. |
| `S005_03_negative_artifact_examples` | 10 | `review_sessions/S005_03_negative_artifact_examples.csv` | artifact, cosmic-ray-hot-pixel, uncertain | At least 20 high-confidence negative labels across negative sessions. |
| `S006_03_negative_artifact_examples` | 10 | `review_sessions/S006_03_negative_artifact_examples.csv` | artifact, cosmic-ray-hot-pixel, uncertain | At least 20 high-confidence negative labels across negative sessions. |
| `S007_04_strong_single_frame_check` | 10 | `review_sessions/S007_04_strong_single_frame_check.csv` | possible-lightning, artifact, cosmic-ray-hot-pixel, uncertain | Each note explains diffuse/multi-pixel evidence or why the row should stay uncertain. |
| `S008_04_strong_single_frame_check` | 10 | `review_sessions/S008_04_strong_single_frame_check.csv` | possible-lightning, artifact, cosmic-ray-hot-pixel, uncertain | Each note explains diffuse/multi-pixel evidence or why the row should stay uncertain. |
| `S009_05_low_priority_hold` | 15 | `review_sessions/S009_05_low_priority_hold.csv` | artifact, cosmic-ray-hot-pixel, uncertain | No scientific claim is made from this session alone. |
| `S010_05_low_priority_hold` | 15 | `review_sessions/S010_05_low_priority_hold.csv` | artifact, cosmic-ray-hot-pixel, uncertain | No scientific claim is made from this session alone. |

## Safe Interpretation

A completed session creates human review evidence. It still does not confirm new lightning unless the labels, temporal behavior, geometry, and scientific review all support the claim.