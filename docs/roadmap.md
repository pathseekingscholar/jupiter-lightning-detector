# Scientific Roadmap

## Current Stage

The project is at the validation and review-queue stage.

Current strengths:

- OPUS/PDS data access is automated.
- Calibrated Cassini ISS products are used instead of screenshots.
- Published lightning marks are recovered.
- All candidates, not only matches, are saved for review.
- OPUS nearby-date coverage is documented, including dates with no NAC/HAL
  result for the selected query.
- Review artifacts now include temporal tracks, artifacts, single-frame
  candidates, and published-match examples.
- Human-in-the-loop training files now exist, so reviewer labels can become
  reproducible model-training data instead of informal notes.

Current limitation:

- Unmatched detections are not yet scientifically validated lightning.

## Next Milestone: Manual Review

Review the 106-row scientific review queue.

For each candidate:

- inspect the thumbnail and parent frame,
- label as possible lightning, artifact, cosmic ray/hot pixel, or uncertain,
- write a short reason,
- keep false positives as examples rather than deleting them.

The first review target is `outputs/detection/active_learning_queue.csv`. It
orders the highest-value unlabeled candidates first so human time is spent on
the most useful examples.

## Next Milestone: Label Governance

Before any trained model is introduced, build a clean labeled set:

- all 6 published validation marks reviewed as known lightning,
- at least 50 clear artifacts,
- at least 50 uncertain or possible lightning candidates,
- labels from more than one processed date,
- examples from repeated tracks and single-frame events,
- second review for high-interest possible-lightning candidates.

The label schema is `schemas/candidate_label.schema.json`.

## Next Milestone: Temporal And Geometric Validation

The strongest evidence should come from repeated detections.

Needed upgrades:

- show each track as a frame-by-frame strip,
- estimate whether the apparent motion is consistent across frames,
- map candidate x/y positions to Jupiter latitude/longitude where metadata
  supports it,
- reject tracks that move like image artifacts rather than rotating cloud/storm
  features.

## Next Milestone: Color / Spectrum Context

Once a candidate survives manual and temporal review:

- search nearby OPUS products in other filters,
- compare candidate timing with broadband or adjacent filter images,
- document whether spectrum/color analysis is possible for that event.

## Later Model Comparison

Only after reviewed labels exist, compare:

- current rule-based blob detector,
- temporal detector,
- YOLO or another object detector.

The paper should be about Jovian lightning, not about using a fashionable model.

Any model comparison should report:

- true positives against the published marks,
- false negatives against the published marks,
- human-reviewed false positives,
- reduction in review workload,
- performance on dates not used for training,
- whether temporal/geometric validation improves the candidate list.
