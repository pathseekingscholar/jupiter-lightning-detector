# GitHub Project Board

This generated board converts the research-gate backlog into contributor-facing work lanes. It is not proof that GitHub issues were created remotely; it is the reproducible project-board source for the repo.

## Board Summary

- Total cards: 8
- Geometry / SPICE: 1
- Human Review: 4
- Maintenance: 1
- Model Readiness: 1
- Spectrum Follow-Up: 1

## Lanes

| Lane | Issue | Priority | Dependency | Proof artifact | Owner role |
|---|---|---|---|---|---|
| Geometry / SPICE | `JLD-005` Add candidate pixel-to-Jupiter geometry mapping | `P1` | spice_inputs | `outputs/detection/geometry_input_inventory.md` | geometry/SPICE implementer |
| Human Review | `JLD-001` Label published validation matches as positive examples | `P1` | review_sessions | `outputs/detection/human_review_audit.md` | human reviewer |
| Human Review | `JLD-002` Label negative artifact and hot-pixel examples | `P1` | review_sessions | `outputs/detection/human_review_audit.md` | human reviewer |
| Human Review | `JLD-003` Run first human label import or workbench labeling pass | `P1` | label_import | `outputs/detection/human_review_audit.md` | human reviewer |
| Human Review | `JLD-004` Human-confirm all six published validation marks | `P1` | human_positive_labels | `outputs/detection/human_review_audit.md` | human reviewer |
| Model Readiness | `JLD-006` Hold YOLO/model comparison until reviewed labels exist | `P1` | human_labels | `outputs/detection/training_readiness.md` | modeling lead after labels exist |
| Spectrum Follow-Up | `JLD-007` Review nearby non-HAL filter context after candidate validation | `P2` | candidate_validation | `outputs/detection/nearby_filter_context_report.md` | science reviewer |
| Maintenance | `JLD-008` Keep documentation claim audit clean | `P3` | none | `outputs/detection/doc_claim_audit.md` | maintainer |

## Card Details

### JLD-005 - Add candidate pixel-to-Jupiter geometry mapping

- Lane: Geometry / SPICE
- Gate: `candidate_geometry` (`not_ready`)
- Dependency: `spice_inputs`
- Blocked by: NAIF Cassini kernels and ISS camera assumptions
- Proof command: `.\run.ps1 geometry-inputs; .\run.ps1 geometry-acquisition; .\run.ps1 research-gates`
- Proof artifact: `outputs/detection/geometry_input_inventory.md`
- Owner role: geometry/SPICE implementer

Definition of done:

- [ ] `outputs/detection/geometry_input_inventory.csv` reports projection inputs ready for the target frames.
- [ ] Cassini ISS camera model assumptions are documented.
- [ ] Required local SPICE kernels are present and listed.
- [ ] Candidate x/y coordinates can be mapped to Jupiter latitude/longitude or a documented projection failure.
- [ ] No location-based storm claim is made until this gate is ready.

### JLD-001 - Label published validation matches as positive examples

- Lane: Human Review
- Gate: `human_positive_labels` (`not_ready`)
- Dependency: `review_sessions`
- Blocked by: S001 known validation session must be reviewed
- Proof command: `.\run.ps1 label-summary; .\run.ps1 label-audit; .\run.ps1 research-gates`
- Proof artifact: `outputs/detection/human_review_audit.md`
- Owner role: human reviewer

Definition of done:

- [ ] All six published validation candidates are labeled `known-lightning` after visual review.
- [ ] `outputs/detection/candidate_label_summary.csv` reports at least 6 positive labels.
- [ ] `outputs/detection/human_review_audit.md` no longer reports `0 of 6` published marks labeled.

### JLD-002 - Label negative artifact and hot-pixel examples

- Lane: Human Review
- Gate: `human_negative_labels` (`not_ready`)
- Dependency: `review_sessions`
- Blocked by: S005 and S006 negative sessions must be reviewed
- Proof command: `.\run.ps1 label-summary; .\run.ps1 label-audit; .\run.ps1 research-gates`
- Proof artifact: `outputs/detection/human_review_audit.md`
- Owner role: human reviewer

Definition of done:

- [ ] At least 20 clear artifacts or cosmic-ray/hot-pixel examples are labeled.
- [ ] `candidate_label_summary.csv` reports at least 20 negative labels.
- [ ] Review notes explain why each negative is not lightning.

### JLD-003 - Run first human label import or workbench labeling pass

- Lane: Human Review
- Gate: `saved_human_labels` (`not_ready`)
- Dependency: `label_import`
- Blocked by: At least one completed review session CSV
- Proof command: `.\run.ps1 label-summary; .\run.ps1 label-audit; .\run.ps1 research-gates`
- Proof artifact: `outputs/detection/human_review_audit.md`
- Owner role: human reviewer

Definition of done:

- [ ] Labels are saved through the workbench or imported from CSV.
- [ ] `candidate_labels.csv`, `candidate_labels_grouped.csv`, and `candidate_label_summary.csv` are regenerated.
- [ ] Each saved row has reviewer, confidence, and review note.

### JLD-004 - Human-confirm all six published validation marks

- Lane: Human Review
- Gate: `published_marks_human_confirmed` (`not_ready`)
- Dependency: `human_positive_labels`
- Blocked by: Six known validation candidates need labels
- Proof command: `.\run.ps1 label-summary; .\run.ps1 label-audit; .\run.ps1 research-gates`
- Proof artifact: `outputs/detection/human_review_audit.md`
- Owner role: human reviewer

Definition of done:

- [ ] The six validation candidates are inspected in context.
- [ ] Each row is labeled `known-lightning` with high confidence unless there is a documented reason not to.
- [ ] `research_gate_audit.md` marks `published_marks_human_confirmed` ready.

### JLD-006 - Hold YOLO/model comparison until reviewed labels exist

- Lane: Model Readiness
- Gate: `model_training_readiness` (`not_ready`)
- Dependency: `human_labels`
- Blocked by: 6 positives, 20 negatives, confidence, notes, no unresolved second-review flags
- Proof command: `.\run.ps1 training-readiness; .\run.ps1 research-gates`
- Proof artifact: `outputs/detection/training_readiness.md`
- Owner role: modeling lead after labels exist

Definition of done:

- [ ] `outputs/detection/training_readiness.csv` marks `model_comparison_allowed` ready.
- [ ] At least 6 human-confirmed positive labels and 20 human-confirmed negative labels exist.
- [ ] Training-ready labels include confidence, reviewer notes, and no unresolved second-review flag.
- [ ] Any YOLO or learned model comparison is evaluated against the classical detector baseline.

### JLD-007 - Review nearby non-HAL filter context after candidate validation

- Lane: Spectrum Follow-Up
- Gate: `nearby_filter_followup` (`in_progress`)
- Dependency: `candidate_validation`
- Blocked by: Reviewed candidate labels before spectrum/color follow-up
- Proof command: `.\run.ps1 filters; .\run.ps1 research-gates`
- Proof artifact: `outputs/detection/nearby_filter_context_report.md`
- Owner role: science reviewer

Definition of done:

- [ ] Only human-reviewed candidate rows are linked to nearby non-HAL context.
- [ ] Context images are used as follow-up evidence, not as spectrum proof by themselves.
- [ ] Any color/spectrum claim cites the exact candidate and context images.

### JLD-008 - Keep documentation claim audit clean

- Lane: Maintenance
- Gate: `documentation_claim_safety` (`ready`)
- Dependency: `none`
- Blocked by: nothing explicit
- Proof command: `.\run.ps1 claim-audit; .\run.ps1 research-gates`
- Proof artifact: `outputs/detection/doc_claim_audit.md`
- Owner role: maintainer

Definition of done:

- [ ] `outputs/detection/doc_claim_audit.csv` has zero `unsafe` rows with status `review`.
- [ ] Generated docs do not say new lightning is confirmed before review.

## Safe Interpretation

A board card moving to done means the cited evidence file proves that gate improved. It does not mean new Jupiter lightning has been confirmed.