# Research Readiness Checklist

This checklist is aimed at making the project understandable and useful to
researchers outside this local machine.

## Current Strengths

- Uses OPUS/PDS Cassini ISS data instead of screenshot-only measurements.
- Recovers the six published lightning validation marks.
- Saves all candidates, not just successful matches.
- Provides false-positive and artifact review examples.
- Produces temporal-track summaries and frame strips.
- Provides human-label exports and active-learning queues.

## Not Yet Ready For A Paper Claim

- No unmatched candidate has been manually validated as new lightning.
- Pixel coordinates are not yet mapped to Jupiter latitude/longitude.
- Temporal tracks are first-pass links, not physically registered storm tracks.
- No trained ML model has been evaluated against the baseline yet.
- Candidate score is not a calibrated probability.

## Ready For Research Discussion

The project is ready to discuss as:

> A reproducible candidate-generation and review pipeline for Cassini Jupiter
> night-side lightning imagery, validated against published detections and
> prepared for human-in-the-loop training.

## Next Review Meeting Goals

1. Review the published-match contact sheet.
2. Review the top unmatched temporal-track strip.
3. Label 20-50 candidates across positive, artifact, and uncertain buckets.
4. Decide whether any unmatched temporal tracks deserve geometry follow-up.
5. Decide which nearby-filter searches matter for color/spectrum analysis.
