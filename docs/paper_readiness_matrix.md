# Paper Readiness Matrix

## Current Claim Level

| Claim | Status | Evidence |
|---|---|---|
| The code can process Cassini ISS Jupiter images | Ready | Detector outputs regenerated locally |
| The detector recovers published validation marks | Ready | 6 of 6 known marks recovered |
| The workflow stores human labels | Ready | JSON/CSV label export with reviewer metadata |
| The nearby NAC/HAL OPUS query is documented | Ready | OPUS coverage scan for 2000-12-28 through 2001-01-16 |
| The detector found new lightning | Not ready | Unmatched candidates still need review and validation |
| The project can train YOLO | Not ready | Needs reviewed label set first |
| The project can make color/spectrum claims | Not ready | Needs nearby-filter analysis for validated candidates |

## Method Section Readiness

Ready now:

- data source and OPUS query,
- detector rules,
- validation against published marks,
- review queue generation,
- human-in-the-loop label storage.

Needs more work:

- Jupiter geometry mapping,
- manual review results,
- model comparison after labels,
- scientific interpretation of new candidates,
- color/spectrum context.

## What A Researcher Should Trust Today

They can trust that the current run is reproducible on the local machine, that
the published validation marks are recovered in the generated outputs, and that
the repo now documents where the current claims stop.

## What A Researcher Should Not Trust Yet

They should not trust unmatched detector candidates as discoveries. Those are
review targets.
