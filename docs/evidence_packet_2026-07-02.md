# Evidence Packet - 2026-07-02

## One-Sentence Status

I now have a reproducible Cassini Jupiter lightning candidate workflow that
recovers the six published validation marks, processes all nine nearby
NAC/HAL OPUS date windows found by the current query, and produces review and
training files for human-in-the-loop validation.

## Safe Claim

The detector recovers the published validation marks and creates a reviewable
candidate set.

## Unsafe Claim

The detector has discovered new lightning. That has not been proven yet.

## Current Processed Coverage

The OPUS nearby-date coverage scan checked 2000-12-28 through 2001-01-16 for
Cassini ISS Narrow Angle Camera H-alpha/HAL Jupiter results. It found nine
available dates, and all nine are processed:

- 2000-12-31
- 2001-01-01
- 2001-01-04
- 2001-01-05
- 2001-01-08
- 2001-01-09
- 2001-01-10
- 2001-01-11
- 2001-01-13

## Current Numbers

- Images processed: 221
- Raw bright regions saved: 196,233
- Review candidates after artifact filters: 12,611
- Published lightning marks recovered: 6 of 6
- Scientific review queue rows: 106
- Training manifest rows: 106
- Active-learning/review-priority rows: 106

## Known-Match Validation

The detector recovered all six published Table 2 validation marks within the
current 8-pixel validation radius:

| Image | Published x/y | Detector x/y | Offset px |
|---|---:|---:|---:|
| N1357029177 | 731, 211 | 731.37, 212.49 | 1.54 |
| N1357029177 | 846, 397 | 847.00, 402.23 | 5.32 |
| N1357810970 | 955, 357 | 955.53, 354.96 | 2.11 |
| N1357810970 | 951, 330 | 951.80, 333.08 | 3.18 |
| N1357885387 | 775, 341 | 769.65, 339.50 | 5.56 |
| N1357885387 | 775, 316 | 776.00, 318.00 | 2.24 |

## What The Detector Measures

- x/y image position
- brightness
- local contrast / SNR
- blob size
- artifact flags
- candidate score
- temporal track length
- pixel-space motion consistency

## Human-In-The-Loop Workflow

1. The detector proposes candidates.
2. A human reviewer labels each candidate.
3. The workbench saves label, confidence, reviewer, review time, and notes.
4. The export script builds `training_manifest.csv`.
5. Future models, including YOLO, can be compared against the explainable
   baseline only after enough reviewed labels exist.

## Files To Show

- `outputs/detection/review_packet.md`
- `outputs/detection/scientific_review_queue.csv`
- `outputs/detection/training_manifest.csv`
- `outputs/detection/active_learning_queue.csv`
- `outputs/detection/known_match_report.csv`
- `outputs/detection/temporal_track_summary.csv`
- `outputs/detection/review_artifacts/temporal_track_strips.png`
- `docs/current_results_summary.md`
- `docs/human_in_the_loop_training.md`
- `docs/model_card_baseline_detector.md`
- `docs/dataset_card.md`

## GitHub Roadmap Issues

- Issue 1: Review the 106-row scientific candidate queue
  <https://github.com/pathseekingscholar/jupiter-lightning-detector/issues/1>
- Issue 2: Map candidate x/y positions to Jupiter geometry
  <https://github.com/pathseekingscholar/jupiter-lightning-detector/issues/2>
- Issue 3: Search nearby filters for color and spectrum context
  <https://github.com/pathseekingscholar/jupiter-lightning-detector/issues/3>
- Issue 4: Compare YOLO only after enough human labels exist
  <https://github.com/pathseekingscholar/jupiter-lightning-detector/issues/4>
- Issue 5: Add clean reproduction artifact for first-time researchers
  <https://github.com/pathseekingscholar/jupiter-lightning-detector/issues/5>

## Meeting Explanation

What I would say:

> Since our last discussion, I focused less on making the interface prettier
> and more on making the detector scientifically reviewable. The detector now
> processes all nine nearby NAC/H-alpha OPUS date windows returned by the query,
> recovers all six published validation marks, and saves a review queue instead
> of claiming new lightning automatically. I also added the human-review and
> training-data layer, so when I label a candidate as possible lightning,
> artifact, hot pixel, or uncertain, that decision is saved with confidence and
> notes for future model comparison.

## Next Scientific Gate

The next gate is manual review of the 106-row scientific review queue, followed
by temporal and geometric validation. A new-lightning claim should only happen
after that.
