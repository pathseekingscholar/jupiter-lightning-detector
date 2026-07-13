# Manuscript Claim Matrix

This generated matrix keeps paper-facing language tied to current evidence. It is meant to stop accidental overclaiming while still making the useful results easy to state.

## Summary

- Supported claims: 4
- Limited claims: 1
- Not-supported claims: 3

## Claim Table

| ID | Section | Status | Safe wording | Evidence | Proof command |
|---|---|---|---|---|---|
| `C01` | Data | `supported` | The current reproducible run processes 221 Cassini ISS NAC/H-alpha frames. | `outputs/detection/detection_summary.csv` | `.\run.ps1 detect-all; .\run.ps1 exports; .\run.ps1 research-gates` |
| `C02` | Validation | `supported` | The detector recovers 6 of 6 published validation marks within the configured matching radius. | `outputs/detection/known_match_report.csv` | `.\run.ps1 exports; .\run.ps1 research-gates` |
| `C03` | Candidate Review | `supported` | The workflow curates 12611 review candidates and a 106-row first-pass review plan. | `outputs/detection/first_pass_review_plan.csv` | `.\run.ps1 review; .\run.ps1 review-plan; .\run.ps1 review-sessions` |
| `C04` | Human Review | `not_supported` | Current saved labels: 0; positives: 0; negatives: 0. | `outputs/detection/candidate_label_summary.csv` | `.\run.ps1 label-summary; .\run.ps1 label-audit; .\run.ps1 training-readiness` |
| `C05` | Geometry | `not_supported` | 0 projection-ready; 221 blocked; 0 candidate maps | `outputs/detection/geometry_input_inventory.csv` | `.\run.ps1 geometry-inputs; .\run.ps1 geometry-acquisition; .\run.ps1 research-gates` |
| `C06` | Spectrum | `limited` | The workflow has 769 nearby non-HAL context rows for follow-up review after candidate validation. | `outputs/detection/nearby_filter_context.csv` | `.\run.ps1 filters; .\run.ps1 research-gates` |
| `C07` | Modeling | `not_supported` | 0 positives; 0 negatives; 0 training-ready | `outputs/detection/training_readiness.csv` | `.\run.ps1 training-readiness; .\run.ps1 research-gates` |
| `C08` | Limitations | `supported` | Unmatched candidates are review targets until human, temporal, and geometry checks support a stronger claim. | `outputs/detection/research_gate_audit.csv` | `.\run.ps1 research-gates; .\run.ps1 claim-audit` |

## Unsafe Wording To Avoid

| ID | Do not say | Why not |
|---|---|---|
| `C01` | The pipeline processes every relevant Cassini Jupiter image. | Expand OPUS coverage only with documented query criteria and regenerated manifests. |
| `C02` | The detector proves all lightning has been found. | Keep threshold changes tied to known-match recall and report any missed validation mark. |
| `C03` | The detector found thousands of lightning events. | Complete human review sessions and preserve false positives for analysis. |
| `C04` | The model has been trained on reviewed labels. | Review S001 for known positives and S005-S006 for negative examples, then import labels. |
| `C05` | The detector already maps each candidate to a Jovian storm location. | Acquire/document NAIF Cassini SPICE kernels and ISS camera model assumptions before location claims. |
| `C06` | The project measured the color spectrum of new lightning events. | Use nearby-filter products only after candidates survive human, temporal, and geometry review. |
| `C07` | YOLO has been trained and outperforms the classical detector. | Create at least 6 positive and 20 negative high-confidence reviewed labels with notes. |
| `C08` | The pipeline discovered new lightning. | Manually review and validate candidates before moving any unmatched row into a discovery table. |

## Safe Bottom Line

The current project supports a reproducible detector and review workflow that recovers published validation marks. It does not yet support a confirmed new-lightning, Jovian-location, spectrum, or trained-model claim.