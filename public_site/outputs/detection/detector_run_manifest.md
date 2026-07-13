# Detector run manifest

Generated: 2026-07-13T15:50:03.227129+00:00

## What ran

A custom classical computer-vision detector written in Python with NumPy and Pillow. YOLO, reinforcement learning, deep learning, and OpenCV are not used in the current detector.

## Measured outputs

- Date windows: 9
- Images processed: 221
- Connected bright regions retained: 196233
- Review candidates after artifact/ranking rules: 12611
- Prioritized first-pass review rows: 106
- Published validation rows in that first pass: 6

## Fixed parameters

- `background_blur_radius_px`: 18.0
- `detection_snr_threshold`: 7.0
- `review_snr_threshold`: 8.0
- `minimum_review_blob_area_px`: 3
- `maximum_component_area_px`: 500
- `maximum_track_displacement_px`: 85.0
- `maximum_track_gap_minutes`: 12.0

## Interpretation

Every connected bright region is retained in per-date candidates.csv. Artifact rules and ranking produce the review-candidate tables. first_pass_review_plan.py then selects a manageable 106-row validation and review batch; 106 is not the number of detections and not a confirmed-lightning count.

Human labels are stored as evidence. They do not silently retrain or modify this detector.
