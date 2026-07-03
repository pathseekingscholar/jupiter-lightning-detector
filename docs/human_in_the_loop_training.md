# Human-In-The-Loop Training Plan

## Purpose

The current detector is an explainable candidate generator. The long-term goal
is a reusable planetary-image pipeline where machine detection and human review
improve each other over repeated runs.

The loop is:

```text
Cassini image
-> detector proposes candidates
-> human reviewer labels candidates
-> labels become validation/training data
-> model or thresholds are updated
-> detector runs again
```

## Current Status

The project is not using YOLO or reinforcement learning yet. It is generating a
reviewable training foundation:

- `scientific_review_queue.csv`
- `training_manifest.csv`
- `active_learning_queue.csv`
- `candidate_labels.csv`
- `candidate_labels.json`

## Human Reviewer Labels

Use these labels consistently:

| Label | Meaning |
|---|---|
| known-lightning | Candidate matches a published lightning mark. |
| possible-lightning | Candidate is scientifically interesting and should survive to deeper review. |
| artifact | Candidate is likely an image or processing artifact. |
| cosmic-ray-hot-pixel | Candidate looks like a single-frame detector hit or hot pixel. |
| uncertain | Not enough evidence yet. |

The human note should answer:

- Why was this kept or rejected?
- Is it multi-pixel or single-pixel?
- Does it repeat across frames?
- Does it move plausibly?
- Is there any nearby missing line, edge effect, streak, or obvious artifact?

## Training Data Products

`training_manifest.csv` joins candidate measurements with human-label status.
It separates:

- validation examples from published lightning,
- likely negative examples from artifact buckets,
- active-learning examples from uncertain unmatched candidates.

`active_learning_queue.csv` is the next human-review queue. It prioritizes:

1. top unmatched temporal tracks,
2. strong single-frame candidates,
3. likely artifacts,
4. known validation matches.

## How This Becomes ML Later

After enough human labels exist, the project can compare models:

- current rule-based detector,
- stricter threshold detector,
- temporal-track detector,
- YOLO or another object detector.

YOLO would not replace science review. It would propose boxes faster. Human
review and validation would still decide whether a candidate is usable.

## Minimum Label Set Before Training

Do not train a deep model from the six published marks alone. A useful first
training set should include:

- all six published validation marks,
- at least 50 reviewed artifacts,
- at least 50 reviewed uncertain/possible candidates,
- examples from multiple dates,
- repeated-frame candidates and single-frame false positives.

Until then, the current classical detector remains the baseline.
