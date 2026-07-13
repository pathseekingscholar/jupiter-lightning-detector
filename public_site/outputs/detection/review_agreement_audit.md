# Review Agreement Audit

This audit separates saved human labels from labels that are strong enough to use for validation or training. A single saved label is useful evidence, but it is not automatically consensus.

## Current Label State

- Total saved labels: 0
- Positive labels: 0
- Negative labels: 0
- Labels needing second review: 0
- Training-ready labels: 0

## Rules

- A training-ready label must be high confidence, have a note, and not be marked as needing second review.
- Possible-lightning labels still need scientific validation before any discovery claim.
- Disagreements or uncertain labels should stay out of training splits until resolved.

## Metrics

| Metric | Status | Value | Meaning | Next action |
|---|---|---:|---|---|
| `total_saved_labels` | `not_started` | 0 | All saved human labels. | Start labeling from the first-pass review batches. |
| `positive_labels` | `needs_work` | 0 | Known or possible lightning labels. | Human-confirm the six published validation marks first. |
| `negative_labels` | `needs_work` | 0 | Artifact or cosmic-ray/hot-pixel labels. | Label clear negatives for false-positive analysis. |
| `uncertain_labels` | `observed` | 0 | Reviewed but unresolved labels. | Use second review, temporal checks, or geometry before training. |
| `needs_second_review` | `ok` | 0 | Labels explicitly marked for another reviewer. | Prioritize these before using labels for training. |
| `high_confidence_labels` | `observed` | 0 | Labels marked high confidence. | Use with notes and no second-review flag for first validation splits. |
| `labels_with_notes` | `observed` | 0 | Labels with human review notes. | Require notes for training-ready labels. |
| `training_ready_labels` | `not_ready` | 0 | High-confidence labels with notes and no second-review flag. | Need at least 6 positives plus 20 negatives before model comparison. |