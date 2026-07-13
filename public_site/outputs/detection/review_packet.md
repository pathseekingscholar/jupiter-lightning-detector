# Cassini Jupiter Lightning Review Packet

## Current Safe Claim

I have a reproducible candidate-detection and review workflow for Cassini Jupiter night-side images. The detector recovers the published validation detections and saves matched, unmatched, and artifact-flagged candidates for review.

I am not claiming new lightning yet. Unmatched candidates are a review pool.

## Current Numbers

- Images processed: 221
- Raw bright regions saved: 196233
- Review candidates after artifact filters: 12611
- Published marks recovered: 6 of 6
- Dataset manifest rows: 221
- Scientific review queue rows: 106

## Date Summary

| Date | Images | Raw candidates | Review candidates | Published matches | Unmatched review |
|---|---:|---:|---:|---:|---:|
| 2000-12-31 | 12 | 5035 | 565 | 0 | 565 |
| 2001-01-01 | 23 | 9447 | 1094 | 2 | 1092 |
| 2001-01-04 | 17 | 3888 | 483 | 0 | 483 |
| 2001-01-05 | 22 | 4784 | 573 | 0 | 573 |
| 2001-01-08 | 54 | 115644 | 6310 | 0 | 6310 |
| 2001-01-09 | 11 | 7491 | 370 | 0 | 370 |
| 2001-01-10 | 26 | 5880 | 472 | 2 | 470 |
| 2001-01-11 | 31 | 6737 | 418 | 2 | 416 |
| 2001-01-13 | 25 | 37327 | 2326 | 0 | 2326 |

## Review Categories

| Category | Count | Meaning |
|---|---:|---|
| published_match | 6 | Detector candidates nearest to the published lightning marks. |
| top_unmatched_temporal_track | 30 | Repeated candidate tracks that do not match the published answer key. |
| strong_single_frame_candidate | 30 | Bright candidates without temporal confirmation yet. |
| likely_artifact | 40 | Candidates with artifact flags such as single-pixel, too-small, sharp, or streak-like. |

## Contact Sheets

- likely_artifact: `outputs\detection\review_artifacts\likely_artifact.png`
- published_match: `outputs\detection\review_artifacts\published_match.png`
- strong_single_frame_candidate: `outputs\detection\review_artifacts\strong_single_frame_candidate.png`
- top_unmatched_temporal_track: `outputs\detection\review_artifacts\top_unmatched_temporal_track.png`
- temporal_track_strips: `outputs\detection\review_artifacts\temporal_track_strips.png`

## Known-Match Evidence

| Image | Published x/y | Nearest detector x/y | Offset px | Recovered? | Candidate |
|---|---:|---:|---:|---|---|
| N1357029177 | 731.0, 211.0 | 731.37, 212.49 | 1.54 | yes | 1357029177-0148 |
| N1357029177 | 846.0, 397.0 | 847.00, 402.23 | 5.32 | yes | 1357029177-0219 |
| N1357810970 | 955.0, 357.0 | 955.53, 354.96 | 2.11 | yes | 1357810970-0239 |
| N1357810970 | 951.0, 330.0 | 951.80, 333.08 | 3.18 | yes | 1357810970-0228 |
| N1357885387 | 775.0, 341.0 | 769.65, 339.50 | 5.56 | yes | 1357885387-0218 |
| N1357885387 | 775.0, 316.0 | 776.00, 318.00 | 2.24 | yes | 1357885387-0203 |

## Strongest Temporal Tracks

These are still review targets, not confirmed storms. Frame repetition is useful because cosmic rays usually do not persist across multiple nearby frames.

| Date | Track | Frames | Start image | End image | Net motion px | Score |
|---|---|---:|---|---|---:|---:|
| 2001-01-01 | T0635 | 3 | N1357037371 | N1357038121 | -42.21, 54.22 | 0.8013 |
| 2001-01-01 | T0209 | 3 | N1357019483 | N1357020233 | -109.65, -42.46 | 0.7946 |
| 2001-01-01 | T0466 | 3 | N1357028427 | N1357029177 | -2.67, -7.44 | 0.7925 |
| 2001-01-04 | T0184 | 3 | N1357331473 | N1357332223 | 125.72, 6.95 | 0.7747 |
| 2000-12-31 | T0353 | 3 | N1356990399 | N1356991149 | 21.37, -75.84 | 0.7672 |
| 2001-01-01 | T0237 | 3 | N1357019483 | N1357020233 | 9.42, -56.24 | 0.7638 |
| 2001-01-01 | T0216 | 3 | N1357019483 | N1357020233 | -57.59, -116.30 | 0.7620 |
| 2001-01-01 | T0577 | 3 | N1357032899 | N1357033649 | -23.23, -5.14 | 0.7618 |
| 2001-01-01 | T0363 | 3 | N1357023955 | N1357024705 | -61.09, -59.67 | 0.7586 |
| 2000-12-31 | T0019 | 3 | N1356976983 | N1356977733 | 18.51, -18.89 | 0.7556 |

## Threshold Sensitivity

The threshold sweep is a false-positive control table. It shows how many candidates remain when SNR and blob-size requirements are tightened. A stricter rule can reduce the review queue, but it must not erase the published validation detections.

Key output file: `outputs/detection/threshold_sweep.csv`.

## Files To Open During Review

- `outputs/detection/dataset_manifest.csv`
- `outputs/detection/detection_summary.csv`
- `outputs/detection/known_match_report.csv`
- `outputs/detection/scientific_review_queue.csv`
- `outputs/detection/temporal_track_summary.csv`
- `outputs/detection/threshold_sweep.csv`
- `outputs/detection/review_artifacts/*.png`
- `outputs/detection/<date>/candidate_contact_sheet.png`
