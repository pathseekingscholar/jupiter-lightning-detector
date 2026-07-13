# Review Session Audit

This audit checks whether the generated review-session CSVs have enough human-review information to import safely. It does not create labels and it does not judge lightning by itself.

## Summary

- Sessions found: 10
- Candidate rows across sessions: 106
- Filled human labels: 0
- Import-ready sessions: 0
- Not-started sessions: 10

## Required For Import

A reviewed row should have a valid `human_label`, valid `confidence`, `reviewer`, and `review_note`. Training-ready rows must also be high confidence and not marked as needing second review.

## Sessions

| Session | Batch | Status | Rows | Filled | Import-ready rows | Training-ready rows | Next action |
|---|---|---|---:|---:|---:|---:|---|
| `S001_01_known_validation_positive` | `01_known_validation_positive` | `not_started` | 6 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S001_01_known_validation_positive.csv and fill reviewer labels. |
| `S002_02_temporal_persistence_check` | `02_temporal_persistence_check` | `not_started` | 10 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S002_02_temporal_persistence_check.csv and fill reviewer labels. |
| `S003_02_temporal_persistence_check` | `02_temporal_persistence_check` | `not_started` | 10 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S003_02_temporal_persistence_check.csv and fill reviewer labels. |
| `S004_02_temporal_persistence_check` | `02_temporal_persistence_check` | `not_started` | 10 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S004_02_temporal_persistence_check.csv and fill reviewer labels. |
| `S005_03_negative_artifact_examples` | `03_negative_artifact_examples` | `not_started` | 10 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S005_03_negative_artifact_examples.csv and fill reviewer labels. |
| `S006_03_negative_artifact_examples` | `03_negative_artifact_examples` | `not_started` | 10 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S006_03_negative_artifact_examples.csv and fill reviewer labels. |
| `S007_04_strong_single_frame_check` | `04_strong_single_frame_check` | `not_started` | 10 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S007_04_strong_single_frame_check.csv and fill reviewer labels. |
| `S008_04_strong_single_frame_check` | `04_strong_single_frame_check` | `not_started` | 10 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S008_04_strong_single_frame_check.csv and fill reviewer labels. |
| `S009_05_low_priority_hold` | `05_low_priority_hold` | `not_started` | 15 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S009_05_low_priority_hold.csv and fill reviewer labels. |
| `S010_05_low_priority_hold` | `05_low_priority_hold` | `not_started` | 15 | 0 | 0 | 0 | Open outputs/detection/review_sessions/S010_05_low_priority_hold.csv and fill reviewer labels. |

## Safe Interpretation

A session marked `import_ready` can be imported into the label store. It still does not confirm new lightning unless the resulting labels, temporal evidence, geometry, and scientific review support that claim.