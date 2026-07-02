# Current Results Summary - 2026-07-02

## Safe Claim

I have a reproducible candidate-detection and review workflow for Cassini ISS
Jupiter night-side H-alpha images. The detector recovers the six published
validation marks and now produces a larger review pool from nine date windows.

I am not claiming new lightning yet.

## Processed Date Windows

| Date | Images | Raw candidates | Review candidates | Published matches | Unmatched review |
|---|---:|---:|---:|---:|---:|
| 2000-12-31 | 12 | 5,035 | 565 | 0 | 565 |
| 2001-01-01 | 23 | 9,447 | 1,094 | 2 | 1,092 |
| 2001-01-04 | 17 | 3,888 | 483 | 0 | 483 |
| 2001-01-05 | 22 | 4,784 | 573 | 0 | 573 |
| 2001-01-08 | 54 | 115,644 | 6,310 | 0 | 6,310 |
| 2001-01-09 | 11 | 7,491 | 370 | 0 | 370 |
| 2001-01-10 | 26 | 5,880 | 472 | 2 | 470 |
| 2001-01-11 | 31 | 6,737 | 418 | 2 | 416 |
| 2001-01-13 | 25 | 37,327 | 2,326 | 0 | 2,326 |

Totals:

- Images processed: 221
- Raw bright regions saved: 196,233
- Review candidates after artifact filters: 12,611
- Published marks recovered: 6 of 6
- Scientific review queue rows: 106

## Known-Match Evidence

The known-match report gives the nearest detector candidate to every published
lightning mark. All six are recovered within the current 8-pixel validation
radius.

| Image | Published x/y | Detector x/y | Offset px |
|---|---:|---:|---:|
| N1357029177 | 731, 211 | 731.37, 212.49 | 1.54 |
| N1357029177 | 846, 397 | 847.00, 402.23 | 5.32 |
| N1357810970 | 955, 357 | 955.53, 354.96 | 2.11 |
| N1357810970 | 951, 330 | 951.80, 333.08 | 3.18 |
| N1357885387 | 775, 341 | 769.65, 339.50 | 5.56 |
| N1357885387 | 775, 316 | 776.00, 318.00 | 2.24 |

## Review Artifacts

`outputs/detection/scientific_review_queue.csv` groups review examples into:

- published matches
- top unmatched temporal tracks
- strong single-frame candidates
- likely artifacts

The generated contact sheets are local outputs:

- `outputs/detection/review_artifacts/published_match.png`
- `outputs/detection/review_artifacts/top_unmatched_temporal_track.png`
- `outputs/detection/review_artifacts/strong_single_frame_candidate.png`
- `outputs/detection/review_artifacts/likely_artifact.png`
- `outputs/detection/review_artifacts/temporal_track_strips.png`

## What Still Has To Be Proved

The unmatched candidates are not discoveries. To become scientifically credible,
they need manual review, repeated-frame validation, and eventually geometry that
maps x/y pixels to Jupiter latitude/longitude.
