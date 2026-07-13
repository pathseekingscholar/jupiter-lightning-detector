# Research Gate Audit

This report summarizes what is ready for scientific use and what still blocks stronger claims. It is generated from current output files, not from memory.

## Summary

- Ready gates: 5
- In-progress gates: 1
- Not-ready gates: 6

## Gates

| Gate | Status | Value | Evidence | Interpretation | Next action |
|---|---|---:|---|---|---|
| `data_processed` | `ready` | 221 | `outputs/detection/detection_summary.csv` | Detector outputs exist for the current 221-image processed set. | Regenerate detector outputs if this drops below the expected processed-image count. |
| `published_match_recovery` | `ready` | 6 of 6 | `outputs/detection/known_match_report.csv` | The detector recovers the published validation marks in the generated outputs. | Do not tune thresholds in a way that loses known validation marks. |
| `first_pass_review_queue` | `ready` | 106 | `outputs/detection/first_pass_review_plan.csv` | A manageable first-pass human-review queue exists. | Regenerate review-plan exports and preserve every curated candidate. |
| `human_positive_labels` | `not_ready` | 0 | `outputs/detection/candidate_label_summary.csv` | Positive labels are needed before training or claiming reviewed positives. | Label the six published validation matches first. |
| `human_negative_labels` | `not_ready` | 0 | `outputs/detection/candidate_label_summary.csv` | Negative labels are needed for false-positive analysis and later model comparison. | Label at least 20 clear artifacts or cosmic-ray/hot-pixel examples. |
| `saved_human_labels` | `not_ready` | 0 | `outputs/detection/candidate_labels.csv` | Saved labels convert detector candidates into review evidence. | Use the workbench or CSV import to save labels with reviewer notes. |
| `published_marks_human_confirmed` | `not_ready` | 0 of 6 | `outputs/detection/human_review_audit.csv` | Published matches should be explicitly confirmed by human labels. | Mark the six validation candidates as known-lightning after visual check. |
| `documentation_claim_safety` | `ready` | 0 | `outputs/detection/doc_claim_audit.csv` | Project-facing docs should not overclaim unsupported discoveries. | Fix any unsafe claim-audit rows before presenting or publishing. |
| `nearby_filter_followup` | `in_progress` | 769 | `outputs/detection/nearby_filter_context.csv` | Nearby non-HAL context exists for follow-up color/spectrum review. | Use this only after candidates survive human and temporal validation. |
| `candidate_geometry` | `not_ready` | 0 projection-ready; 221 blocked; 0 candidate maps | `outputs/detection/geometry_input_inventory.csv` | Candidate-level geometry is blocked by missing projection inputs. missing_documented_iss_camera_model: 221; missing_local_spice_kernels: 221 | Collect/document the Cassini ISS camera model and local SPICE kernels before making location-based storm claims. |
| `model_training_readiness` | `not_ready` | 0 positives; 0 negatives; 0 training-ready | `outputs/detection/training_readiness.csv` | Learned detector comparison is allowed only after human-confirmed positives, negatives, notes, and confidence fields exist. | Finish human labels before training a learned detector. |
| `evidence_integrity` | `ready` | 10 ready; 0 in progress; 0 not ready | `outputs/detection/evidence_integrity_audit.csv` | Reviewer-facing evidence files should be internally consistent before review or presentation. | Fix any not-ready evidence-integrity checks before relying on the review packet. |

## Safe Conclusion

The detector/review workflow is reproducible and validation-oriented. It is not yet a confirmed new-lightning discovery workflow because human labels, negative examples, and candidate-level geometry remain incomplete.