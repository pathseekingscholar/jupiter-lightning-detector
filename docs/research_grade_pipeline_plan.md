# Cassini Jupiter Lightning Detection: Research-Grade Pipeline Plan

## Core Objective

I am building a scientifically validated pipeline to identify and characterize
candidate lightning events in Cassini Jupiter images. The point is not to make a
fancy AI demo. The point is to recover known lightning, find credible overlooked
candidates, and produce measurements that can support planetary-science analysis.

Working objective:

> Develop a reliable method to identify and characterize lightning in Cassini
> Jupiter images, then use that method to discover additional candidate events
> and study their properties.

## Why This Can Become Science

Dyudina et al. (2004) reported Cassini ISS night-side H-alpha observations of
Jupiter lightning. The paper is scientifically interesting because the lightning
is connected to storm clouds, repeated activity, optical power, and the possible
weakness of the H-alpha line compared with broadband optical lightning.

The publishable direction is therefore not "I used YOLO." The publishable
direction is:

1. Build a repeatable detector.
2. Validate it against the published detections.
3. Measure false positives and false negatives.
4. Review unmatched candidates.
5. If credible new candidates survive review, characterize them:
   - time
   - location
   - persistence
   - brightness
   - size
   - possible storm association
   - possible color or spectral behavior

## Data Sources

- OPUS / PDS Ring-Moon Systems Node for Cassini ISS metadata and products.
- Cassini ISS calibrated image products and labels.
- Dyudina et al. (2004), Icarus 172, 24-36, for published lightning reference
  detections.
- Local extracted paper notes:
  `docs/published_paper_extracted_notes.txt`

OPUS matters because the pipeline needs reproducible input data, not screenshots.
The OPUS API supports metadata retrieval, file lookup, result counts, and search
queries. That lets the project record exactly which images were processed.

## Current Detector

The current method is classical computer vision:

```text
Cassini calibrated image
-> stretch / brighten night side
-> estimate smooth background
-> subtract background
-> compute local signal-to-noise
-> find connected bright blobs
-> measure blob properties
-> flag obvious artifacts
-> save every candidate
-> rank review candidates
-> compare against published detections
-> human review
```

The detector measures:

| Measurement | Meaning | Why it matters |
|---|---|---|
| image_id | Cassini image identifier | Keeps every candidate traceable |
| candidate_id | Unique detector candidate ID | Lets labels and notes attach to one object |
| x, y | Pixel location | Needed for paper-coordinate validation |
| brightness | Peak local SNR | Shows how strongly the blob stands above background |
| blob_size | Connected-pixel area | Helps separate diffuse blobs from one-pixel hits |
| mean_snr | Average local SNR inside the blob | Measures local contrast |
| sharpness | Peak divided by mean | Sharp tiny events often resemble cosmic rays |
| elongation | Stretched-line shape metric | Long streaks are often artifacts |
| artifact flags | Rule-based warnings | Makes rejection explainable |
| candidate score | Review priority | Not a calibrated probability |

## Current Output Products

For each detector date:

- `outputs/detection/<date>/candidates.csv`
- `outputs/detection/<date>/review_candidates.csv`
- `outputs/detection/<date>/candidate_contact_sheet.png`
- `outputs/detection/<date>/summary.json`

Across reviewed candidates:

- `outputs/detection/candidate_labels.csv`
- `outputs/detection/candidate_labels.json`

Across detector settings:

- `outputs/detection/threshold_sweep.csv`
- `outputs/detection/known_match_report.csv`
- `outputs/detection/scientific_review_queue.csv`
- `outputs/detection/temporal_track_summary.csv`
- `outputs/detection/review_packet.md`
- `outputs/detection/review_artifacts/*.png`

The threshold sweep is a sensitivity check. It asks how many candidates remain
when the SNR threshold or minimum blob size is made stricter, and whether the
published lightning detections are still recovered.

The known-match report is the validation table. It records the nearest detector
candidate to each published lightning mark, the pixel offset, and whether that
offset is within the current 8-pixel recovery radius.

The temporal-track summary is the next scientific bridge. It records candidates
that appear in linked frames, because repeated detections are more useful than a
single bright spot when separating possible storms from cosmic rays.

The scientific review queue is the human-review starting point. It intentionally
contains examples from four buckets: published matches, top unmatched temporal
tracks, strong single-frame candidates, and likely artifacts.

The all-candidates CSV is intentionally large because non-matches are not thrown
away. They are useful for false-positive analysis and later model training.

## Current Processed Dates

| Date | Role |
|---|---|
| 2000-12-31 | Expanded near-flyby search date |
| 2001-01-01 | Published validation date |
| 2001-01-04 | Expanded near-flyby search date |
| 2001-01-05 | Expanded near-flyby search date |
| 2001-01-08 | Expanded near-flyby search date |
| 2001-01-09 | Expanded near-flyby search date |
| 2001-01-10 | Published validation date |
| 2001-01-11 | Published validation date |
| 2001-01-13 | Broader review/search date |

The current validation result is that the generated detector outputs recover the
six published marks from the known validation dates. The current expanded run
processed 221 images and produced 12,611 review candidates. That is not the
same as discovering new lightning; it means the detector can reproduce the known
answer key and create a much larger review pool.

## Definitions

- True positive: the detector finds a published lightning spot.
- False negative: the detector misses a published lightning spot.
- False positive: the detector flags something later reviewed as not lightning.
- Candidate: something worth reviewing, not confirmed lightning.
- Unmatched candidate: a detector candidate that is not in the paper; it is not
  automatically false.
- Candidate score: review priority, not a real probability unless calibrated
  later.

## Human Review Loop

The review loop is the bridge between detection and science.

1. Detector produces candidates.
2. Human reviewer labels candidates:
   - known lightning
   - possible lightning
   - artifact
   - cosmic ray / hot pixel
   - uncertain
3. Labels are saved to CSV and JSON.
4. Reviewed labels become a training and validation set.
5. Only after this label set exists does it make sense to compare learned models.

This is how the project can later support YOLO or another model without pretending
that deep learning is already the science.

## Model Comparison Plan

Do not start with YOLO as the main claim. Use it later as one comparison method.

| Method | Use | Strength | Weakness |
|---|---|---|---|
| Current blob detector | Baseline detector and review generator | Explainable and fast | Many false positives |
| Difference / temporal detector | Check repeat behavior across nearby frames | Uses the storm-repeat clue | Needs registration/navigation |
| Classical blob + tracking | Candidate storm tracking | Scientifically interpretable | Sensitive to thresholds |
| YOLO / object detector | Later candidate proposal model | Can learn visual patterns from labels | Needs enough labeled examples |
| Human review | Final scientific gate | Uses context and judgment | Slow, must be documented |

YOLO in plain English:

YOLO is an object-detection model. It looks at an image and draws boxes around
objects it thinks it recognizes. For each box, it gives a confidence score. In
this project, YOLO would eventually learn what possible Jupiter lightning looks
like from labeled examples. It should not be the first method because the project
does not yet have enough trusted labels.

## Publishable Roadmap

### Level 1: Engineering

Build a reliable detector and save every candidate with reproducible metadata.

Deliverables:

- all-candidates CSV
- candidate thumbnails
- review candidates
- detector rules
- source image IDs

### Level 2: Validation

Recover published detections and measure the errors.

Deliverables:

- true-positive table
- false-negative table
- false-positive labels
- threshold sensitivity notes

### Level 3: New Candidates

Review unmatched candidates and keep only those with credible evidence.

Deliverables:

- possible-lightning label list
- artifact examples
- uncertain examples
- temporal-repeat checks

### Level 4: Science

Use validated candidates to measure new properties.

Possible analyses:

- flash/storm frequency
- latitude distribution
- storm persistence
- motion with Jupiter rotation
- relationship to day-side clouds
- H-alpha brightness
- possible color or spectral behavior if nearby filters can be matched

## Immediate Next Implementation Tasks

1. Add a dataset manifest that lists every processed image, date, OPUS ID, time,
   filter, and local file path.
2. Add a candidate-review export grouped by label.
3. Add a temporal-repeat page that shows the same track across frames.
4. Add a navigation/geometry stage: convert x/y candidates to Jupiter latitude
   and longitude where metadata supports it.
5. Search nearby filters for each candidate time to support color/spectrum work.
6. Add a threshold-sweep validation report to show how many candidates appear
   when SNR and blob-size cutoffs change.

## Current Claim Language

Safe claim:

> I built an explainable candidate-detection and review pipeline for Cassini
> Jupiter night-side images. It recovers the published lightning detections in
> the validation set and produces saved candidate tables, thumbnails, and human
> review labels for unmatched detections.

Unsafe claim:

> The detector discovered new lightning.

That can only be said after manual review, temporal checks, and scientific
characterization.

## Sources

- OPUS archive: https://opus.pds-rings.seti.org/
- OPUS API guide: https://opus.pds-rings.seti.org/apiguide.pdf
- Dyudina et al. (2004), ADS: https://ui.adsabs.harvard.edu/abs/2004Icar..172...24D/abstract
- Dyudina et al. (2004), ScienceDirect page:
  https://www.sciencedirect.com/science/article/abs/pii/S0019103504002428
- Local paper copy used for extracted notes:
  `C:\Users\vedar\Downloads\lightning_cassini_published.pdf`
