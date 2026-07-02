# Research Log - 2026-07-02

## Decision

I am reframing the project as a planetary-science pipeline, not an AI demo.

The working scientific objective is:

> Develop a reliable method to identify and characterize lightning in Cassini
> Jupiter images, then use that method to discover additional candidate events
> and study their properties.

## What Changed In The Workbench

- The first tab is now an About page instead of a professor-directed explanation.
- The app language now says the detector produces review candidates, not
  confirmed lightning.
- The workflow emphasizes:
  - recover published detections
  - save all candidates
  - label false positives
  - identify false negatives
  - review unmatched candidates
  - look for repeated candidates across frames
- The roadmap now points toward spectrum/color analysis after candidate
  validation.

## Why This Matters

The detector itself is only useful if it enables credible science. A simple
classical detector plus careful human review can be more valuable than a more
complex model if it finds and documents real candidate storms.

## Current Safe Claim

I have a reproducible candidate-detection and review workflow. It recovers the
published lightning detections in the validation set and saves candidate tables,
thumbnails, and review labels for further analysis.

## Current Unsafe Claim

I should not claim new lightning yet. Unmatched candidates are not automatically
false, but they are also not automatically discoveries.

## Next Implementation Direction

1. Build a dataset manifest for all processed images.
2. Add grouped exports for human labels.
3. Add a temporal-track view that shows candidates across frames.
4. Add image geometry / latitude-longitude mapping.
5. Search nearby filters for possible spectrum and color analysis.
