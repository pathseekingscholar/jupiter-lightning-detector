# Training Readiness Report

This report answers whether the project is ready to train or compare a learned detector such as YOLO. It is generated from saved human labels and review artifacts.

## Summary

- Ready gates: 3
- Not-ready gates: 6
- Model comparison status: `not_ready`
- Model comparison value: 0 positives; 0 negatives; 0 training-ready

## Gates

| Gate | Status | Value | Minimum | Evidence | Next action |
|---|---|---:|---:|---|---|
| `saved_labels_exist` | `not_ready` | 0 | 1 | `outputs/detection/candidate_label_summary.csv` | Save reviewer labels through the workbench or label CSV import. |
| `positive_examples` | `not_ready` | 0 | 6 | `outputs/detection/candidate_label_summary.csv` | Label the six published validation matches first. |
| `negative_examples` | `not_ready` | 0 | 20 | `outputs/detection/candidate_label_summary.csv` | Label at least 20 clear artifacts or cosmic-ray/hot-pixel rows. |
| `training_ready_labels` | `not_ready` | 0 | 26 | `outputs/detection/review_agreement_audit.csv` | Require high confidence, reviewer notes, and no second-review flag for first training-ready rows. |
| `active_learning_queue` | `ready` | 106 | 1 | `outputs/detection/active_learning_queue.csv` | Review top active-learning rows after known positives and clear negatives. |
| `validation_split` | `ready` | 6 | 6 | `outputs/detection/training_manifest.csv` | Keep published matches separate from candidate training rows. |
| `negative_review_batch` | `ready` | 20 | 20 | `outputs/detection/review_labeling_checklist.csv` | Use the negative artifact batch to create first negative labels. |
| `model_comparison_allowed` | `not_ready` | 0 positives; 0 negatives; 0 training-ready | 6 positives; 20 negatives; 26 training-ready | `outputs/detection/candidate_label_summary.csv` | Finish human labels before training a learned detector. |
| `notes_and_confidence` | `not_ready` | 0 high confidence; 0 with notes; 0 uncertain | 26 high confidence and noted labels | `outputs/detection/review_agreement_audit.csv` | Do not use unlabeled or weakly noted rows as training truth. |

## Safe Interpretation

The current detector is an explainable candidate generator. YOLO or another learned model should not be trained or compared until human labels include at least the six published validation positives, at least twenty clear negatives, and training-ready notes/confidence for those rows.

## First Labeling Target

1. Label the six `01_known_validation_positive` rows as `known-lightning` only after visual confirmation.
2. Label at least twenty `03_negative_artifact_examples` rows as `artifact` or `cosmic-ray-hot-pixel` when visually clear.
3. Leave ambiguous temporal candidates as `uncertain` until temporal and geometry checks improve.