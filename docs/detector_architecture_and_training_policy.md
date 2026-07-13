# Detector architecture and training policy

## System boundary

The project has three separate parts. They should not be described as one AI system.

1. The local detector downloads calibrated Cassini images, measures bright regions, links nearby regions across frames,
   and creates review queues.
2. The public review site shows a fixed evidence snapshot and sends human labels to the shared review sheet.
3. A future training experiment may use reviewed labels, but only after the project owner deliberately starts a new,
   versioned run.

The public website does not run the detector. Saving a review does not change the detector.

## Current detector

The current detector is custom classical computer vision written in Python. It uses NumPy for numerical operations and
Pillow for image loading, Gaussian background estimation, and review graphics. It does not use YOLO, reinforcement
learning, deep learning, or OpenCV.

For each calibrated Cassini frame, the program:

1. stretches the valid pixels between the 2nd and 99.8th percentiles;
2. estimates the broad background with an 18-pixel Gaussian blur;
3. subtracts that background and estimates noise with the median absolute deviation;
4. keeps pixels at or above 7 sigma;
5. joins touching pixels with an eight-neighbor connected-component search;
6. measures position, area, peak and integrated SNR, sharpness, and elongation;
7. flags single pixels, very small regions, sharp cosmic-ray-like events, and long streaks;
8. links reviewable regions across frames within 85 pixels and 12 minutes; and
9. ranks tracks using persistence, motion consistency, diffuse size, SNR, and artifact penalties.

The score is a ranking score. It is not a calibrated probability that a candidate is lightning.

## What the counts mean

The current nine date-window runs processed 221 images. They retained 196,233 connected bright regions before strict
review filtering. Artifact and ranking rules produced 12,611 review candidates. The 106-row first-pass queue is a
deliberately small review plan containing published validation examples, temporal candidates, artifacts, strong
single-frame candidates, and holdout examples. It is not 106 lightning flashes.

Run `python detector_run_audit.py` to regenerate these counts from local outputs instead of copying them by hand.

## Human labels and later training

Reviewer labels are evidence, not immediate model updates. Before any training run, labels need duplicate checks,
reviewer-agreement checks, class-balance inspection, and separation by observation sequence so nearly identical frames
cannot leak between training and testing.

When enough trustworthy labels exist, the first learned baseline should use the detector's measured blob and temporal
features in a simple model such as logistic regression or a random forest. A YOLO experiment becomes useful only after
there are enough consistently boxed positive and negative image examples. Any learned model must be compared against
the fixed classical detector on a held-out sequence-level test set.

Automatic retraining remains disabled. A human initiates training, records the dataset version, reviews metrics and
errors, and decides whether the new model is allowed to generate future review queues.

## Compute choice

The 221-image classical detector is practical on the local computer. Andromeda is not required for ordinary review or
small reruns. It becomes useful for scanning a much larger archive, producing ISIS geometry in bulk, running parameter
sweeps, or training several learned models. Moving to Andromeda should preserve the same command-line inputs, manifests,
and outputs rather than creating a second scientific method.
