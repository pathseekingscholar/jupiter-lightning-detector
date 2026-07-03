# Model Card: Explainable Baseline Detector

## Model Type

This is not a deep-learning model. It is an explainable classical computer
vision detector used as the baseline before YOLO or any trained model.

## Intended Use

The detector finds bright candidate regions in Cassini Jupiter night-side
images and saves them for human review. It is meant to reduce manual search
work, not replace scientific judgment.

## Inputs

- Calibrated Cassini ISS image.
- Image metadata and OPUS ID.
- Optional published validation marks for known detections.

## Detector Features

- Brightness: how bright the candidate is.
- Local contrast: how much brighter it is than nearby background.
- Blob size: how many connected pixels form the candidate.
- Signal-to-noise ratio: brightness relative to local background variation.
- Shape metrics: whether the object is compact, diffuse, or streak-like.
- Artifact flags: single-pixel, too-small, sharp, or streak-like warnings.
- Temporal link quality: whether nearby candidates appear in consecutive
  frames with reasonably consistent pixel motion.

## Outputs

- Candidate x/y coordinate.
- SNR and brightness measurements.
- Blob size and shape information.
- Artifact flags.
- Candidate score.
- Review category.
- Optional match to published lightning marks.

## What The Score Means

The score is a review ranking. It is not a calibrated probability of lightning.
High score means "look at this earlier." It does not mean "confirmed lightning."

## Validation Status

The current detector recovers 6 of 6 published validation marks across the
generated outputs. This validates that the pipeline can recover the known
answer-key examples, but it does not prove that unmatched candidates are real.

## Failure Modes

- Cosmic rays and hot pixels can look bright in one frame.
- Limb and edge artifacts can create false bright regions.
- Noise can create many low-quality candidates.
- Pixel-space tracks can link unrelated candidates if the scene is crowded.
- Real lightning may be missed if it is too faint, too diffuse, or below the
  chosen threshold.

## Future Model Comparison

YOLO or another trained detector should only be introduced after enough human
labels exist. Any trained model must be compared against this baseline on:

- known published detections recovered,
- false positives reviewed by humans,
- false negatives against known marks,
- review workload reduction,
- temporal/geometric consistency,
- performance on dates not used for training.
