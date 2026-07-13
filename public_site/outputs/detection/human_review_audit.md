# Human Review And Training Audit

This report answers the review-loop question: what has a human actually labeled, what is still only a detector candidate, and what is ready to become training data.

## Current State

- Candidate rows available for review: 106
- Human labels saved inside the current manifest: 0
- Positive training examples: 0
- Negative training examples: 0
- Uncertain review examples: 0
- Unlabeled candidates remaining: 106
- Published validation marks labeled positive: 0 of 6

## What Counts As Positive And Negative

- Positive: `known-lightning` or `possible-lightning` after human review.
- Negative: `artifact` or `cosmic-ray-hot-pixel` after human review.
- Uncertain: useful for follow-up, but not clean training data yet.
- Unlabeled: detector output only; it is not evidence of lightning by itself.

## Why This Matters

A future YOLO or learned detector needs both positive and negative examples. The current classical detector proposes candidates, but the human label is the scientific gate. Until enough labels exist, the project should not claim that a trained AI model understands lightning.

## Decision-Matrix Queues

| Queue | Count | Meaning |
|---|---:|---|
| `confirm_known_validation_mark` | 6 | Decision-matrix action count. |
| `priority_temporal_review` | 23 | Decision-matrix action count. |
| `review_as_negative_example` | 40 | Decision-matrix action count. |
| `single_frame_visual_review` | 30 | Decision-matrix action count. |
| `temporal_review` | 7 | Decision-matrix action count. |

## Saved Label Counts

No human labels have been saved yet for the current manifest.

## Safe Claim

The detector has produced a reviewable candidate set and a structure for human-in-the-loop training. Human labels are the next required evidence layer before claiming new lightning or training a YOLO-style model.