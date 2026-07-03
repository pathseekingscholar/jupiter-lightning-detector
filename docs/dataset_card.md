# Dataset Card: Cassini Jupiter Lightning Candidate Review Set

## Purpose

This dataset is a review set for possible lightning in Cassini ISS Jupiter
images. It is designed to help a human reviewer inspect detector candidates,
compare them with published lightning detections, and build labels for later
model training.

It is not a confirmed catalog of new lightning.

## Source Data

- Mission/instrument: Cassini Imaging Science Subsystem.
- Target: Jupiter.
- Camera/filter priority: Narrow Angle Camera, H-alpha/HAL.
- Primary archive: OPUS / PDS Rings Node.
- Validation source: Dyudina et al. (2004), Table 2 published lightning marks.

## Current Coverage

The current OPUS nearby-date scan covers 2000-12-28 through 2001-01-16.
For the Cassini ISS NAC/HAL Jupiter query, 9 dates returned available frames,
and all 9 are processed by the detector:

- 2000-12-31
- 2001-01-01
- 2001-01-04
- 2001-01-05
- 2001-01-08
- 2001-01-09
- 2001-01-10
- 2001-01-11
- 2001-01-13

## Generated Tables

- `dataset_manifest.csv`: image-level provenance and processing status.
- `detection_summary.csv`: date-level image and candidate counts.
- `known_match_report.csv`: detector recovery of the published marks.
- `scientific_review_queue.csv`: curated review rows for humans.
- `training_manifest.csv`: candidate rows joined with label state.
- `active_learning_queue.csv`: unlabeled rows that should be reviewed first.

## Labels

Allowed human labels are:

- `known-lightning`
- `possible-lightning`
- `artifact`
- `cosmic-ray-hot-pixel`
- `uncertain`

A `possible-lightning` label means "worth scientific follow-up." It does not
mean "new discovery."

## Known Limitations

- Current coordinates are image x/y coordinates, not yet mapped to Jupiter
  latitude/longitude.
- Current temporal tracks are pixel-space links, not full geometric storm
  tracking on the rotating planet.
- OPUS coverage is scoped to a nearby NAC/HAL Jupiter query, not the full
  Cassini Jupiter flyby.
- Unmatched candidates are unresolved review items. They are not automatically
  false positives, and they are not confirmed lightning.

## Ethical And Scientific Use

Use this dataset to support review, reproducibility, and model comparison. Do
not cite unmatched detector candidates as planetary science discoveries until
they pass human review, temporal/geometric validation, and source-image audit.
