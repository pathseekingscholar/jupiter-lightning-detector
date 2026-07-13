# Evidence Integrity Audit

This audit checks that reviewer-facing evidence files are internally consistent. It does not decide whether a candidate is lightning.

## Summary

- Ready checks: 10
- In-progress checks: 0
- Not-ready checks: 0

## Checks

| Check | Status | Value | Expected | Evidence | Next action |
|---|---|---:|---|---|---|
| `review_plan_dossier_row_match` | `ready` | 106 plan; 106 dossier | matching nonzero counts | `outputs/detection/first_pass_review_plan.csv` | Regenerate review and review-plan exports if counts differ. |
| `blind_packet_key_row_match` | `ready` | 106 packet; 106 key; 106 plan | all equal to first-pass review count | `outputs/detection/blind_review_packet.csv` | Regenerate blind-review packet if packet/key counts differ. |
| `blind_reconciliation_row_match` | `ready` | 106 reconciliation; 106 packet | reconciliation count equals packet count | `outputs/detection/blind_review_reconciliation.csv` | Run .\run.ps1 blind-reconcile after changing the blind packet. |
| `blind_id_integrity` | `ready` | 0 duplicate blind IDs; 0 missing keys | 0 duplicates and 0 missing keys | `outputs/detection/blind_review_key.csv` | Regenerate blind review packet and key together. |
| `review_crop_url_shape` | `ready` | 106 crop URLs; 0 malformed | all crop URLs contain image, x, y, and crop | `outputs/detection/first_pass_review_plan.csv` | Fix crop URL generation before reviewer use. |
| `review_image_products_exist` | `ready` | 45 referenced images; 0 missing calibrated products | all referenced images have local calibrated image and label | `outputs/detection/first_pass_review_plan.csv` | Download/regenerate missing OPUS calibrated products before review. |
| `review_artifact_images_valid` | `ready` | 5 valid; 0 invalid | all review artifact PNGs open successfully | `outputs/detection/review_artifacts` | Regenerate review metrics/artifact contact sheets. |
| `known_positive_batch_size` | `ready` | 6 | 6 | `outputs/detection/review_batches/01_known_validation_positive.csv` | Regenerate first-pass review plan; keep all six known validation marks. |
| `negative_batch_size` | `ready` | 20 | at least 20 | `outputs/detection/review_batches/03_negative_artifact_examples.csv` | Regenerate first-pass review plan with enough clear negative examples. |
| `blind_import_currently_empty` | `ready` | 0 | 0 until blind reviewer labels are filled | `outputs/detection/blind_review_label_import.csv` | If nonzero, inspect reconciliation before importing labels. |

## Safe Interpretation

A ready integrity audit means the evidence package is coherent enough for review. It is not a scientific validation result and does not confirm new lightning.