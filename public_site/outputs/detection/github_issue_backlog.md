# GitHub Issue Backlog

This generated backlog turns the current research gate audit into concrete GitHub-ready issues. It should be regenerated after labels, geometry, or validation outputs change.

| ID | Priority | Title | Gate | Status | Labels | Evidence |
|---|---|---|---|---|---|---|
| `JLD-001` | `P1` | Label published validation matches as positive examples | `human_positive_labels` | `not_ready` | `candidate-review,validation` | `outputs/detection/candidate_label_summary.csv` |
| `JLD-002` | `P1` | Label negative artifact and hot-pixel examples | `human_negative_labels` | `not_ready` | `candidate-review,false-positive-analysis` | `outputs/detection/candidate_label_summary.csv` |
| `JLD-003` | `P1` | Run first human label import or workbench labeling pass | `saved_human_labels` | `not_ready` | `candidate-review,data-management` | `outputs/detection/candidate_labels.csv` |
| `JLD-004` | `P1` | Human-confirm all six published validation marks | `published_marks_human_confirmed` | `not_ready` | `candidate-review,validation` | `outputs/detection/human_review_audit.csv` |
| `JLD-005` | `P1` | Add candidate pixel-to-Jupiter geometry mapping | `candidate_geometry` | `not_ready` | `geometry,science-validation` | `outputs/detection/geometry_input_inventory.csv` |
| `JLD-006` | `P1` | Hold YOLO/model comparison until reviewed labels exist | `model_training_readiness` | `not_ready` | `model-comparison,human-labels,validation` | `outputs/detection/training_readiness.csv` |
| `JLD-007` | `P2` | Review nearby non-HAL filter context after candidate validation | `nearby_filter_followup` | `in_progress` | `data-provenance,spectrum-followup` | `outputs/detection/nearby_filter_context.csv` |
| `JLD-008` | `P3` | Keep documentation claim audit clean | `documentation_claim_safety` | `ready` | `documentation,science-validation` | `outputs/detection/doc_claim_audit.csv` |

## Issue Bodies

### JLD-001: Label published validation matches as positive examples

- Gate: `human_positive_labels`
- Current status: `not_ready`
- Current value: 0
- Evidence file: `outputs/detection/candidate_label_summary.csv`
- Labels: `candidate-review,validation`

Why it matters:

Positive labels are needed before training or claiming reviewed positives.

Next action:

Label the six published validation matches first.

Acceptance criteria:

- [ ] All six published validation candidates are labeled `known-lightning` after visual review.
- [ ] `outputs/detection/candidate_label_summary.csv` reports at least 6 positive labels.
- [ ] `outputs/detection/human_review_audit.md` no longer reports `0 of 6` published marks labeled.

### JLD-002: Label negative artifact and hot-pixel examples

- Gate: `human_negative_labels`
- Current status: `not_ready`
- Current value: 0
- Evidence file: `outputs/detection/candidate_label_summary.csv`
- Labels: `candidate-review,false-positive-analysis`

Why it matters:

Negative labels are needed for false-positive analysis and later model comparison.

Next action:

Label at least 20 clear artifacts or cosmic-ray/hot-pixel examples.

Acceptance criteria:

- [ ] At least 20 clear artifacts or cosmic-ray/hot-pixel examples are labeled.
- [ ] `candidate_label_summary.csv` reports at least 20 negative labels.
- [ ] Review notes explain why each negative is not lightning.

### JLD-003: Run first human label import or workbench labeling pass

- Gate: `saved_human_labels`
- Current status: `not_ready`
- Current value: 0
- Evidence file: `outputs/detection/candidate_labels.csv`
- Labels: `candidate-review,data-management`

Why it matters:

Saved labels convert detector candidates into review evidence.

Next action:

Use the workbench or CSV import to save labels with reviewer notes.

Acceptance criteria:

- [ ] Labels are saved through the workbench or imported from CSV.
- [ ] `candidate_labels.csv`, `candidate_labels_grouped.csv`, and `candidate_label_summary.csv` are regenerated.
- [ ] Each saved row has reviewer, confidence, and review note.

### JLD-004: Human-confirm all six published validation marks

- Gate: `published_marks_human_confirmed`
- Current status: `not_ready`
- Current value: 0 of 6
- Evidence file: `outputs/detection/human_review_audit.csv`
- Labels: `candidate-review,validation`

Why it matters:

Published matches should be explicitly confirmed by human labels.

Next action:

Mark the six validation candidates as known-lightning after visual check.

Acceptance criteria:

- [ ] The six validation candidates are inspected in context.
- [ ] Each row is labeled `known-lightning` with high confidence unless there is a documented reason not to.
- [ ] `research_gate_audit.md` marks `published_marks_human_confirmed` ready.

### JLD-005: Add candidate pixel-to-Jupiter geometry mapping

- Gate: `candidate_geometry`
- Current status: `not_ready`
- Current value: 0 projection-ready; 221 blocked; 0 candidate maps
- Evidence file: `outputs/detection/geometry_input_inventory.csv`
- Labels: `geometry,science-validation`

Why it matters:

Candidate-level geometry is blocked by missing projection inputs. missing_documented_iss_camera_model: 221; missing_local_spice_kernels: 221

Next action:

Collect/document the Cassini ISS camera model and local SPICE kernels before making location-based storm claims.

Acceptance criteria:

- [ ] `outputs/detection/geometry_input_inventory.csv` reports projection inputs ready for the target frames.
- [ ] Cassini ISS camera model assumptions are documented.
- [ ] Required local SPICE kernels are present and listed.
- [ ] Candidate x/y coordinates can be mapped to Jupiter latitude/longitude or a documented projection failure.
- [ ] No location-based storm claim is made until this gate is ready.

### JLD-006: Hold YOLO/model comparison until reviewed labels exist

- Gate: `model_training_readiness`
- Current status: `not_ready`
- Current value: 0 positives; 0 negatives; 0 training-ready
- Evidence file: `outputs/detection/training_readiness.csv`
- Labels: `model-comparison,human-labels,validation`

Why it matters:

Learned detector comparison is allowed only after human-confirmed positives, negatives, notes, and confidence fields exist.

Next action:

Finish human labels before training a learned detector.

Acceptance criteria:

- [ ] `outputs/detection/training_readiness.csv` marks `model_comparison_allowed` ready.
- [ ] At least 6 human-confirmed positive labels and 20 human-confirmed negative labels exist.
- [ ] Training-ready labels include confidence, reviewer notes, and no unresolved second-review flag.
- [ ] Any YOLO or learned model comparison is evaluated against the classical detector baseline.

### JLD-007: Review nearby non-HAL filter context after candidate validation

- Gate: `nearby_filter_followup`
- Current status: `in_progress`
- Current value: 769
- Evidence file: `outputs/detection/nearby_filter_context.csv`
- Labels: `data-provenance,spectrum-followup`

Why it matters:

Nearby non-HAL context exists for follow-up color/spectrum review.

Next action:

Use this only after candidates survive human and temporal validation.

Acceptance criteria:

- [ ] Only human-reviewed candidate rows are linked to nearby non-HAL context.
- [ ] Context images are used as follow-up evidence, not as spectrum proof by themselves.
- [ ] Any color/spectrum claim cites the exact candidate and context images.

### JLD-008: Keep documentation claim audit clean

- Gate: `documentation_claim_safety`
- Current status: `ready`
- Current value: 0
- Evidence file: `outputs/detection/doc_claim_audit.csv`
- Labels: `documentation,science-validation`

Why it matters:

Project-facing docs should not overclaim unsupported discoveries.

Next action:

Fix any unsafe claim-audit rows before presenting or publishing.

Acceptance criteria:

- [ ] `outputs/detection/doc_claim_audit.csv` has zero `unsafe` rows with status `review`.
- [ ] Generated docs do not say new lightning is confirmed before review.
