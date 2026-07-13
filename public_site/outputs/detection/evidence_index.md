# Evidence Index

This generated index groups the local evidence artifacts by research purpose. It is the first file to open when deciding what a result proves and what it does not prove.

## Summary

- Source manifest: `outputs/detection/provenance_manifest.json`
- Git branch: `codex/science-first-pipeline`
- Git commit: `fd5a1ba3c85e8ab1772d221cab5446b54e802871`
- Indexed artifacts: 95

## Purpose Counts

| Purpose | Artifacts | What it is for |
|---|---:|---|
| `candidate_review` | 12 | Curated candidates and reviewer-facing tables. |
| `claim_safety` | 6 | What can be safely said in a report or manuscript. |
| `coverage` | 3 | Processed dates and input dataset scope. |
| `filter_context` | 3 | Nearby non-H-alpha context for future color/spectrum follow-up. |
| `geometry` | 8 | What is needed before pixel candidates can become Jupiter locations. |
| `human_labels` | 29 | Human label templates, sessions, audits, blind review, and agreement checks. |
| `key_findings` | 3 | Meeting-ready current findings generated from the evidence CSVs. |
| `other` | 10 | Artifacts not matched to a specific purpose bucket. |
| `project_management` | 4 | Issue/project-board exports for collaborators. |
| `temporal_validation` | 6 | Frame-to-frame track evidence and temporal-review questions. |
| `training_readiness` | 4 | Whether reviewed labels are sufficient for learned-model comparison. |
| `validation` | 4 | Published-match recovery, threshold sensitivity, and detector run summaries. |
| `visual_artifacts` | 3 | PNG contact sheets and visual review aids. |

## Open These First

| Question | Start with | Why |
|---|---|---|
| What did the detector process? | `outputs/detection/detection_summary.csv` | Run counts and published-match totals. |
| What are the current key findings? | `outputs/detection/current_key_findings.md` | Generated meeting brief tied to evidence files. |
| Did it recover known lightning? | `outputs/detection/known_match_report.csv` | Six published validation rows with offsets. |
| What should a human review? | `outputs/detection/first_pass_review_plan.md` | Small, ordered review batches. |
| Are review sessions complete? | `outputs/detection/review_session_audit.md` | Shows missing labels, notes, confidence, and import readiness. |
| Which temporal tracks matter? | `outputs/detection/temporal_validation_plan.md` | Prioritized repeated tracks with review questions. |
| Can we claim Jupiter coordinates? | `outputs/detection/geometry_acquisition_checklist.md` | Lists missing SPICE/camera inputs. |
| What can a paper safely say? | `outputs/detection/manuscript_claim_matrix.md` | Supported, limited, and not-supported claims. |

## Artifact Index

| Purpose | Path | Rows | Bytes | Safe use |
|---|---|---:|---:|---|
| `coverage` | `outputs/detection/dataset_manifest.csv` | 221 | 58658 | Use to explain dataset scope and processed dates. |
| `validation` | `outputs/detection/detection_summary.csv` | 9 | 794 | Use to state detector recovery of published marks and current run counts. |
| `validation` | `outputs/detection/threshold_sweep.csv` | 216 | 14403 | Use to state detector recovery of published marks and current run counts. |
| `validation` | `outputs/detection/known_match_report.csv` | 6 | 1215 | Use to state detector recovery of published marks and current run counts. |
| `temporal_validation` | `outputs/detection/temporal_track_summary.csv` | 7344 | 1976601 | Use to prioritize repeated tracks for review; not enough for discovery alone. |
| `candidate_review` | `outputs/detection/scientific_review_queue.csv` | 106 | 21201 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `training_readiness` | `outputs/detection/training_manifest.csv` | 106 | 21342 | Use to decide whether model comparison is allowed. |
| `training_readiness` | `outputs/detection/active_learning_queue.csv` | 106 | 21674 | Use to decide whether model comparison is allowed. |
| `other` | `outputs/detection/review_metrics_summary.csv` | 21 | 1637 | Inspect before using; purpose was not classified automatically. |
| `candidate_review` | `outputs/detection/review_decision_matrix.csv` | 106 | 24144 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `temporal_validation` | `outputs/detection/temporal_track_quality.csv` | 7344 | 1282155 | Use to prioritize repeated tracks for review; not enough for discovery alone. |
| `validation` | `outputs/detection/threshold_recommendations.csv` | 24 | 2258 | Use to state detector recovery of published marks and current run counts. |
| `candidate_review` | `outputs/detection/candidate_review_dossier.csv` | 106 | 29567 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `candidate_review` | `outputs/detection/candidate_review_dossier.html` |  | 56823 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `geometry` | `outputs/detection/geometry_readiness.csv` | 221 | 70902 | Use to explain why location claims are blocked or ready. |
| `geometry` | `outputs/detection/geometry_readiness_report.md` |  | 4561 | Use to explain why location claims are blocked or ready. |
| `geometry` | `outputs/detection/candidate_geometry_plan.csv` | 106 | 25960 | Use to explain why location claims are blocked or ready. |
| `geometry` | `outputs/detection/candidate_geometry_plan.md` |  | 4888 | Use to explain why location claims are blocked or ready. |
| `geometry` | `outputs/detection/geometry_input_inventory.csv` | 221 | 55741 | Use to explain why location claims are blocked or ready. |
| `geometry` | `outputs/detection/geometry_input_inventory.md` |  | 1376 | Use to explain why location claims are blocked or ready. |
| `geometry` | `outputs/detection/geometry_acquisition_checklist.csv` | 7 | 1861 | Use to explain why location claims are blocked or ready. |
| `geometry` | `outputs/detection/geometry_acquisition_checklist.md` |  | 1984 | Use to explain why location claims are blocked or ready. |
| `filter_context` | `outputs/detection/nearby_filter_context.csv` | 769 | 157779 | Use as follow-up context only after candidate validation. |
| `filter_context` | `outputs/detection/nearby_filter_context_report.md` |  | 3938 | Use as follow-up context only after candidate validation. |
| `human_labels` | `outputs/detection/human_review_audit.csv` | 15 | 2364 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/human_review_audit.md` |  | 1894 | Use to track human review progress and training readiness. |
| `candidate_review` | `outputs/detection/first_pass_review_plan.csv` | 106 | 39881 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `candidate_review` | `outputs/detection/first_pass_review_plan.md` |  | 1447 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `candidate_review` | `outputs/detection/first_pass_review_plan.html` |  | 52838 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `human_labels` | `outputs/detection/review_session_plan.csv` | 10 | 5826 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_session_plan.md` |  | 3929 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_session_audit.csv` | 10 | 2229 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_session_audit.md` |  | 3071 | Use to track human review progress and training readiness. |
| `temporal_validation` | `outputs/detection/temporal_validation_plan.csv` | 120 | 101683 | Use to prioritize repeated tracks for review; not enough for discovery alone. |
| `temporal_validation` | `outputs/detection/temporal_validation_plan.md` |  | 24329 | Use to prioritize repeated tracks for review; not enough for discovery alone. |
| `human_labels` | `outputs/detection/blind_review_packet.csv` | 106 | 14064 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/blind_review_key.csv` | 106 | 27169 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/blind_review_packet.md` |  | 1833 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/blind_review_reconciliation.csv` | 106 | 14687 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/blind_review_label_import.csv` | 0 | 223 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/blind_review_reconciliation.md` |  | 1276 | Use to track human review progress and training readiness. |
| `other` | `outputs/detection/evidence_integrity_audit.csv` | 10 | 2033 | Inspect before using; purpose was not classified automatically. |
| `other` | `outputs/detection/evidence_integrity_audit.md` |  | 2716 | Inspect before using; purpose was not classified automatically. |
| `human_labels` | `outputs/detection/review_labeling_checklist.csv` | 5 | 1887 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_labeling_protocol.md` |  | 4438 | Use to track human review progress and training readiness. |
| `training_readiness` | `outputs/detection/training_readiness.csv` | 9 | 2020 | Use to decide whether model comparison is allowed. |
| `training_readiness` | `outputs/detection/training_readiness.md` |  | 2794 | Use to decide whether model comparison is allowed. |
| `claim_safety` | `outputs/detection/doc_claim_audit.csv` | 8 | 1886 | Use when writing reports, abstracts, README text, or meeting summaries. |
| `claim_safety` | `outputs/detection/doc_claim_audit.md` |  | 2137 | Use when writing reports, abstracts, README text, or meeting summaries. |
| `claim_safety` | `outputs/detection/research_gate_audit.csv` | 12 | 2965 | Use when writing reports, abstracts, README text, or meeting summaries. |
| `claim_safety` | `outputs/detection/research_gate_audit.md` |  | 3756 | Use when writing reports, abstracts, README text, or meeting summaries. |
| `claim_safety` | `outputs/detection/manuscript_claim_matrix.csv` | 8 | 3800 | Use when writing reports, abstracts, README text, or meeting summaries. |
| `claim_safety` | `outputs/detection/manuscript_claim_matrix.md` |  | 3831 | Use when writing reports, abstracts, README text, or meeting summaries. |
| `project_management` | `outputs/detection/github_issue_backlog.csv` | 8 | 4972 | Use to coordinate next work; not scientific evidence by itself. |
| `project_management` | `outputs/detection/github_issue_backlog.md` |  | 8142 | Use to coordinate next work; not scientific evidence by itself. |
| `project_management` | `outputs/detection/github_project_board.csv` | 8 | 4581 | Use to coordinate next work; not scientific evidence by itself. |
| `project_management` | `outputs/detection/github_project_board.md` |  | 7846 | Use to coordinate next work; not scientific evidence by itself. |
| `human_labels` | `outputs/detection/review_agreement_audit.csv` | 8 | 1050 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_agreement_audit.md` |  | 1905 | Use to track human review progress and training readiness. |
| `key_findings` | `outputs/detection/key_findings_summary.csv` | 10 | 1544 | Use as the first meeting brief; still follow linked evidence files for proof. |
| `key_findings` | `outputs/detection/current_key_findings.md` |  | 5326 | Use as the first meeting brief; still follow linked evidence files for proof. |
| `key_findings` | `outputs/detection/current_key_findings.html` |  | 7900 | Use as the first meeting brief; still follow linked evidence files for proof. |
| `other` | `outputs/detection/evidence_index.json` |  | 32915 | Inspect before using; purpose was not classified automatically. |
| `other` | `outputs/detection/evidence_index.md` |  | 17370 | Inspect before using; purpose was not classified automatically. |
| `other` | `outputs/detection/reproduction_audit.csv` | 7 | 1218 | Inspect before using; purpose was not classified automatically. |
| `other` | `outputs/detection/reproduction_audit.md` |  | 2100 | Inspect before using; purpose was not classified automatically. |
| `human_labels` | `outputs/detection/candidate_label_template.csv` | 106 | 15920 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/candidate_labels_grouped.csv` | 0 | 223 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/candidate_label_summary.csv` | 11 | 931 | Use to track human review progress and training readiness. |
| `other` | `outputs/detection/review_packet.md` |  | 4633 | Inspect before using; purpose was not classified automatically. |
| `other` | `outputs/detection/review_metrics_report.md` |  | 6022 | Inspect before using; purpose was not classified automatically. |
| `other` | `outputs/detection/review_metrics_report.html` |  | 42975 | Inspect before using; purpose was not classified automatically. |
| `filter_context` | `outputs/detection/opus_nearby_date_coverage.csv` | 20 | 1931 | Use as follow-up context only after candidate validation. |
| `coverage` | `outputs/detection/processed_date_coverage_summary.csv` | 9 | 996 | Use to explain dataset scope and processed dates. |
| `coverage` | `outputs/detection/processed_date_coverage_summary.md` |  | 1913 | Use to explain dataset scope and processed dates. |
| `visual_artifacts` | `outputs/detection/review_artifacts/likely_artifact.png` |  | 210117 | Use for visual inspection and meeting explanation. |
| `visual_artifacts` | `outputs/detection/review_artifacts/published_match.png` |  | 82162 | Use for visual inspection and meeting explanation. |
| `visual_artifacts` | `outputs/detection/review_artifacts/strong_single_frame_candidate.png` |  | 208722 | Use for visual inspection and meeting explanation. |
| `temporal_validation` | `outputs/detection/review_artifacts/temporal_track_strips.png` |  | 322574 | Use to prioritize repeated tracks for review; not enough for discovery alone. |
| `temporal_validation` | `outputs/detection/review_artifacts/top_unmatched_temporal_track.png` |  | 184921 | Use to prioritize repeated tracks for review; not enough for discovery alone. |
| `candidate_review` | `outputs/detection/review_batches/01_known_validation_positive.csv` | 6 | 2616 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `candidate_review` | `outputs/detection/review_batches/02_temporal_persistence_check.csv` | 30 | 11992 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `candidate_review` | `outputs/detection/review_batches/03_negative_artifact_examples.csv` | 20 | 8148 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `candidate_review` | `outputs/detection/review_batches/04_strong_single_frame_check.csv` | 20 | 7236 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `candidate_review` | `outputs/detection/review_batches/05_low_priority_hold.csv` | 30 | 10745 | Use to decide what a human should inspect; do not call rows confirmed lightning. |
| `human_labels` | `outputs/detection/review_sessions/S001_01_known_validation_positive.csv` | 6 | 2867 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_sessions/S002_02_temporal_persistence_check.csv` | 10 | 4562 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_sessions/S003_02_temporal_persistence_check.csv` | 10 | 4565 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_sessions/S004_02_temporal_persistence_check.csv` | 10 | 4565 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_sessions/S005_03_negative_artifact_examples.csv` | 10 | 4564 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_sessions/S006_03_negative_artifact_examples.csv` | 10 | 4562 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_sessions/S007_04_strong_single_frame_check.csv` | 10 | 4100 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_sessions/S008_04_strong_single_frame_check.csv` | 10 | 4094 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_sessions/S009_05_low_priority_hold.csv` | 15 | 5640 | Use to track human review progress and training readiness. |
| `human_labels` | `outputs/detection/review_sessions/S010_05_low_priority_hold.csv` | 15 | 6111 | Use to track human review progress and training readiness. |

## Safe Bottom Line

The evidence package supports a reproducible detector and review workflow. It does not, by itself, confirm new Jupiter lightning.