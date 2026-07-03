# Reviewer Quickstart

## Goal

Review detector candidates without accidentally turning them into discovery
claims.

## Start Here

Open the local workbench:

```powershell
.\run.ps1 app
```

Then open the Detector Automation tab.

## What To Review First

Use these files:

- `outputs/detection/active_learning_queue.csv`
- `outputs/detection/scientific_review_queue.csv`
- `outputs/detection/review_artifacts/temporal_track_strips.png`
- `outputs/detection/review_artifacts/top_unmatched_temporal_track.png`
- `outputs/detection/review_artifacts/likely_artifact.png`
- `outputs/detection/review_artifacts/published_match.png`

Review order:

1. Published validation matches.
2. Top unmatched temporal tracks.
3. Strong single-frame candidates.
4. Likely artifacts.

## Label Choices

- `known-lightning`: published validation mark recovered by the detector.
- `possible-lightning`: scientifically interesting candidate, still unproven.
- `artifact`: likely image/process/instrument artifact.
- `cosmic-ray-hot-pixel`: likely single-frame particle or hot-pixel event.
- `uncertain`: not enough evidence either way.

## What To Write In The Note

Use short, concrete notes:

- diffuse or single-pixel?
- repeated in nearby frames?
- moving consistently?
- near image edge or bad line?
- visible only after aggressive stretch?
- could this be a cosmic ray/hot pixel?

Good note:

```text
Diffuse 4-pixel blob, visible in 3 linked frames, no obvious streak flag.
Needs geometry check before possible lightning claim.
```

Weak note:

```text
Looks good.
```

## What Counts As A Positive Or Negative

A positive training example is a reviewed candidate believed to be lightning or
a published validation mark. A negative training example is a reviewed artifact,
cosmic ray, or hot pixel.

Do not delete negatives. They are necessary for training and false-positive
analysis.

## What Not To Claim

Do not write:

```text
The detector found new lightning.
```

Write:

```text
The detector found unmatched candidates that need human review and
temporal/geometric validation.
```
