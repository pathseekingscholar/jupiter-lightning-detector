# Publication-Oriented Analysis Outline

This is the shape of the project if it grows from a detector workbench into a
scientific result.

## Working Title

Cassini Search for Additional Jovian Lightning Candidates Using Explainable
Image Processing

## Main Question

Can a reproducible detector recover published Cassini lightning detections and
identify additional review-worthy night-side candidates that may support new
measurements of Jovian lightning?

## Paper Logic

1. Cassini observed Jupiter's night side during the 2000-2001 flyby.
2. Published work reported a small set of H-alpha lightning detections.
3. More images exist than were easy to inspect manually.
4. A detector can make the search reproducible by saving every candidate, every
   rejection reason, and every human label.
5. The scientific result only begins after validation and review.

## Methods Section

Describe the current method as an explainable baseline:

```text
Cassini calibrated image
-> contrast stretch
-> local background estimate
-> bright-region detection
-> connected blob formation
-> artifact flagging
-> candidate scoring
-> comparison with published detections
-> human review
```

Important wording:

- This is a classical image-processing detector.
- It is not reinforcement learning.
- It is not YOLO yet.
- The score is a review priority, not a calibrated lightning probability.
- The detector is allowed to produce false positives because false positives are
  part of measuring detector behavior.

## Validation Tables To Produce

| Table | Purpose |
|---|---|
| Dataset manifest | Which images were processed and where they came from |
| Published-match table | Whether known detections were recovered |
| False-negative table | Known detections missed by the detector |
| Candidate summary | Number of raw candidates, review candidates, and artifact flags |
| Human label export | Which candidates were marked possible lightning, artifact, or uncertain |
| Threshold sweep | How results change when SNR/blob-size cutoffs change |

The threshold sweep is important because it turns "the detector has many false
positives" into something measurable. It shows the tradeoff between reducing
the review queue and possibly losing known lightning detections.

## Figures To Produce

1. One-page detector diagram.
2. Example frame with original image, enhanced image, and detected candidates.
3. Contact sheet of top candidates.
4. False-positive examples: hot pixel, cosmic-ray-like dot, streak, edge/missing-line
   artifact.
5. Published-match examples.
6. Temporal track examples if candidates repeat across frames.
7. Later: map of candidate latitude/longitude if geometry is added.

## How New Candidates Become Credible

A new candidate should not be called lightning just because it is bright. It
becomes more credible when it satisfies several independent checks:

- It is not a one-pixel event.
- It is brighter than the local background.
- It has a compact or diffuse blob shape rather than a long streak.
- It appears in multiple nearby frames or has a plausible temporal track.
- It is not sitting on an obvious image artifact.
- It has useful metadata: time, filter, exposure duration, and image ID.
- It can be compared to nearby filters or frames for color/spectrum context.

## Model Comparison

The current detector is the baseline. Later models should be compared against
that baseline, not introduced as magic.

| Method | Question it answers |
|---|---|
| Rule-based blob detector | Can simple, explainable rules recover known lightning? |
| Temporal tracking | Do candidates repeat in a way cosmic rays should not? |
| YOLO or another object detector | Can a trained model reduce review workload after labels exist? |

## Current Best Claim

The current best claim is validation and workflow:

> I built a reproducible candidate-detection and review pipeline for Cassini
> Jupiter night-side images. It recovers the published validation detections and
> saves all matched, unmatched, and artifact-flagged candidates for review.

Do not claim new lightning until candidate labels and temporal checks support it.
