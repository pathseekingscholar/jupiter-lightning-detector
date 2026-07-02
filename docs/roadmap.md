# Scientific Roadmap

## Current Stage

The project is at the validation and review-queue stage.

Current strengths:

- OPUS/PDS data access is automated.
- Calibrated Cassini ISS products are used instead of screenshots.
- Published lightning marks are recovered.
- All candidates, not only matches, are saved for review.
- Review artifacts now include temporal tracks, artifacts, single-frame
  candidates, and published-match examples.

Current limitation:

- Unmatched detections are not yet scientifically validated lightning.

## Next Milestone: Manual Review

Review the 106-row scientific review queue.

For each candidate:

- inspect the thumbnail and parent frame,
- label as possible lightning, artifact, cosmic ray/hot pixel, or uncertain,
- write a short reason,
- keep false positives as examples rather than deleting them.

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
