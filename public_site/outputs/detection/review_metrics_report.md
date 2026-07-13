# Review Metrics Report

This report summarizes the current candidate-review state. It does not confirm new lightning.

## Core Numbers

- Images processed: 221
- Raw bright regions: 196233
- Review candidates: 12611
- Published validation marks recovered: 6
- Unmatched review candidates: 12605
- Scientific review queue rows: 106
- Saved human labels: 0

## Decision Queue

| Next action | Count | Meaning |
|---|---:|---|
| confirm_known_validation_mark | 6 | Published validation target should be checked and labeled first. |
| priority_temporal_review | 23 | Repeated candidate with strong pixel-motion consistency. |
| review_as_negative_example | 40 | Artifact-flagged rows are useful false-positive/negative-training examples. |
| single_frame_visual_review | 30 | Strong bright blob, but single-frame evidence is weak by itself. |
| temporal_review | 7 | Repeated candidate needs visual and geometry review. |

## Temporal Track Quality

| Temporal quality | Count | Meaning |
|---|---:|---|
| moderate_temporal_review | 2981 | Repeated candidates that may be useful after visual inspection. |
| single_frame_not_temporal | 3445 | Single-frame candidates; useful visually but not temporal evidence. |
| strong_temporal_review | 246 | Best temporal-review targets, still not confirmed lightning. |
| weak_temporal_review | 672 | Repeated candidates with weak or irregular evidence. |

## Threshold Tradeoff

These rows summarize stricter detector settings after artifact filtering. The current sweep shows an important warning: the stricter reviewable-only filters do not keep all six published marks. That means strict automatic rejection can create false negatives and must not replace human review.

| Rank | SNR threshold | Min blob | Review candidates | Published matches | Recall | Interpretation |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 7.0 | 8 | 1395 | 5 | 0.833 | misses at least one published mark; risky without review |
| 2 | 7.0 | 5 | 5197 | 5 | 0.833 | misses at least one published mark; risky without review |
| 3 | 7.0 | 3 | 17271 | 5 | 0.833 | misses at least one published mark; risky without review |
| 4 | 7.0 | 1 | 17271 | 5 | 0.833 | misses at least one published mark; risky without review |
| 5 | 8.0 | 8 | 1313 | 3 | 0.500 | too strict for current validation set |
| 6 | 8.0 | 5 | 4819 | 3 | 0.500 | too strict for current validation set |
| 7 | 8.0 | 3 | 15700 | 3 | 0.500 | too strict for current validation set |
| 8 | 8.0 | 1 | 15700 | 3 | 0.500 | too strict for current validation set |
| 9 | 20.0 | 8 | 262 | 2 | 0.333 | too strict for current validation set |
| 10 | 15.0 | 8 | 364 | 2 | 0.333 | too strict for current validation set |

## Top Review Rows

| Rank | Candidate | Image | Date | Action | x/y | SNR | Blob | Score |
|---:|---|---|---|---|---|---:|---:|---:|
| 1 | 1357029177-0148 | N1357029177 | 2001-01-01 | confirm_known_validation_mark | 731.37, 212.49 | 27.55 | 75 | 0.6277 |
| 2 | 1357029177-0219 | N1357029177 | 2001-01-01 | confirm_known_validation_mark | 847.00, 402.23 | 24.75 | 13 | 0.4360 |
| 3 | 1357810970-0228 | N1357810970 | 2001-01-10 | confirm_known_validation_mark | 951.80, 333.08 | 8.14 | 15 | 0.3364 |
| 4 | 1357810970-0239 | N1357810970 | 2001-01-10 | confirm_known_validation_mark | 955.53, 354.96 | 7.92 | 87 | 0.0000 |
| 5 | 1357885387-0203 | N1357885387 | 2001-01-11 | confirm_known_validation_mark | 776.00, 318.00 | 7.50 | 1 | 0.0000 |
| 6 | 1357885387-0218 | N1357885387 | 2001-01-11 | confirm_known_validation_mark | 769.65, 339.50 | 7.06 | 14 | 0.0000 |
| 7 | 1356990399-0202 | N1356990399 | 2000-12-31 | priority_temporal_review | 402.62, 656.20 | 41.20 | 5 | 0.7672 |
| 8 | 1356976983-0161 | N1356976983 | 2000-12-31 | priority_temporal_review | 62.82, 480.68 | 31.42 | 4 | 0.7556 |
| 9 | 1356990399-0080 | N1356990399 | 2000-12-31 | priority_temporal_review | 900.63, 316.07 | 30.93 | 6 | 0.7438 |
| 10 | 1356985927-0141 | N1356985927 | 2000-12-31 | priority_temporal_review | 730.33, 432.12 | 36.45 | 4 | 0.7429 |
| 11 | 1356985927-0245 | N1356985927 | 2000-12-31 | priority_temporal_review | 612.58, 709.56 | 23.17 | 4 | 0.7424 |
| 12 | 1356985927-0162 | N1356985927 | 2000-12-31 | priority_temporal_review | 835.23, 498.82 | 24.92 | 3 | 0.7383 |
| 13 | 1356990399-0013 | N1356990399 | 2000-12-31 | priority_temporal_review | 626.28, 57.49 | 31.06 | 3 | 0.7344 |
| 14 | 1356985927-0123 | N1356985927 | 2000-12-31 | priority_temporal_review | 515.70, 403.81 | 42.51 | 4 | 0.7323 |
| 15 | 1356990399-0030 | N1356990399 | 2000-12-31 | priority_temporal_review | 445.85, 114.86 | 46.63 | 3 | 0.7305 |
| 16 | 1356976983-0147 | N1356976983 | 2000-12-31 | priority_temporal_review | 718.12, 439.44 | 39.54 | 4 | 0.7305 |
| 17 | 1356990399-0193 | N1356990399 | 2000-12-31 | priority_temporal_review | 744.43, 625.61 | 30.54 | 5 | 0.7268 |
| 18 | 1356990399-0086 | N1356990399 | 2000-12-31 | priority_temporal_review | 647.43, 332.24 | 18.02 | 3 | 0.7190 |
| 19 | 1356990399-0056 | N1356990399 | 2000-12-31 | priority_temporal_review | 218.44, 234.51 | 46.05 | 4 | 0.7166 |
| 20 | 1356985927-0197 | N1356985927 | 2000-12-31 | priority_temporal_review | 116.23, 575.74 | 47.55 | 5 | 0.7160 |
| 21 | 1356985927-0308 | N1356985927 | 2000-12-31 | priority_temporal_review | 922.55, 771.33 | 16.06 | 3 | 0.7097 |
| 22 | 1356990399-0263 | N1356990399 | 2000-12-31 | priority_temporal_review | 382.48, 864.12 | 43.14 | 3 | 0.7018 |
| 23 | 1356981455-0275 | N1356981455 | 2000-12-31 | priority_temporal_review | 343.62, 791.13 | 38.33 | 10 | 0.6962 |
| 24 | 1356981455-0109 | N1356981455 | 2000-12-31 | priority_temporal_review | 909.59, 321.38 | 14.01 | 3 | 0.6950 |
| 25 | 1356985927-0012 | N1356985927 | 2000-12-31 | priority_temporal_review | 493.50, 54.00 | 11.67 | 4 | 0.6917 |

## Safe Interpretation

The detector has recovered the known validation marks and produced a prioritized review queue. Unmatched candidates remain review targets, not discoveries.