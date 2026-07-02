# Jupiter Lightning Detector Workbench

This project inspects Cassini ISS Jupiter images for possible lightning. It is a
careful review workbench for extracting new science from Cassini data, not an
automatic discovery engine.

Clear rule: this is not confirmed lightning. The detector saves candidates for
human review.

Scientific objective: build a validated pipeline that identifies candidate
lightning events in Cassini Jupiter images, minimizes false detections, and
supports the discovery and characterization of previously overlooked events.

The initial ground-truth set comes from Dyudina et al. (2004), *Lightning on
Jupiter observed in the H-alpha line by the Cassini imaging science
subsystem*. It contains six detections in three Cassini NAC/HAL images.

## Quick Start

From PowerShell:

```powershell
.\run.ps1 all
.\run.ps1 app
```

The app opens at `http://127.0.0.1:8765`.

Run the detector for the example dates:

```powershell
.\run.ps1 detect-all

# Or run one date at a time:
.\run.ps1 detect -Date 2000-12-31
.\run.ps1 detect -Date 2001-01-01
.\run.ps1 detect -Date 2001-01-04
.\run.ps1 detect -Date 2001-01-05
.\run.ps1 detect -Date 2001-01-08
.\run.ps1 detect -Date 2001-01-09
.\run.ps1 detect -Date 2001-01-10
.\run.ps1 detect -Date 2001-01-11
.\run.ps1 detect -Date 2001-01-13
.\run.ps1 exports
```

## What The App Provides

- About page with the plain-English workflow.
- Upload/select Cassini image support.
- Manual crop and brightness controls for inspection.
- Classical detector output for Dec 31, Jan 1, Jan 4, Jan 5, Jan 8,
  Jan 9, Jan 10, Jan 11, and Jan 13.
- Candidate boxes/circles in crops and contact sheets.
- Candidate review table with image ID, x/y coordinate, brightness, blob size,
  SNR/local contrast, artifact flags, and candidate score.
- Human labels: known lightning, possible lightning, artifact, cosmic ray/hot
  pixel, and uncertain.
- Exportable labels:
  - `outputs/detection/candidate_labels.csv`
  - `outputs/detection/candidate_labels.json`
- Research-grade exports:
  - `outputs/detection/dataset_manifest.csv`
  - `outputs/detection/detection_summary.csv`
  - `outputs/detection/threshold_sweep.csv`
  - `outputs/detection/known_match_report.csv`
  - `outputs/detection/scientific_review_queue.csv`
  - `outputs/detection/temporal_track_summary.csv`
  - `outputs/detection/review_packet.md`
  - `outputs/detection/review_artifacts/*.png`
  - `outputs/detection/candidate_labels_grouped.csv` when human labels exist
- Separate false positive, false negative, and unmatched-candidate sections.
- Known published detections as validation targets.

Uploaded PNG, JPEG, WebP, and BMP images are processed locally in the browser.
They are not sent to OPUS or another external service.

## Detector Pipeline

```text
Cassini image
-> brighten night side
-> find bright spots
-> remove obvious artifacts
-> save candidates
-> human review
-> possible lightning
```

The current detector uses explainable classical computer vision:

- subtract a smooth local background
- detect bright connected regions above local background
- flag single-pixel, too-small, sharp cosmic-ray-like, and streak-like events
- keep uncertain detections for review
- rank candidates with a review score

The candidate score is not a probability unless calibrated later. Unmatched
candidates are not automatically false.

## Publishable Science Path

The paper is not "we used AI." The paper has to be about Jupiter.

1. Engineering: build a detector that saves reproducible candidate evidence.
2. Validation: recover published lightning while measuring false positives and
   false negatives.
3. New candidates: manually validate overlooked detections from unpublished or
   under-reviewed images.
4. Science: use the larger candidate set to study lightning frequency,
   latitude distribution, storm lifetime, temporal evolution, and color or
   spectral behavior.

Classical computer vision, YOLO, or other models are implementation choices.
The project should optimize for scientifically credible lightning detections.

## Current Safe Claim

The current safe claim is:

> The workbench builds a reproducible candidate-detection and review workflow for
> Cassini Jupiter night-side images. It recovers the published validation
> detections and saves candidate tables, thumbnails, and human-review labels for
> unmatched detections.

The current unsafe claim is:

> The detector discovered new lightning.

That claim requires human review, temporal checks, and scientific
characterization first.

## Validation Terms

- True positive: the detector finds known published lightning.
- False negative: the detector misses known published lightning.
- False positive: the detector flags something later reviewed as not lightning.
- Unmatched candidate: not in the paper, not automatically false.

## Important Coordinate Convention

Table 2 in the paper lists pairs that correspond to displayed image `(x, y)`
coordinates. NumPy arrays are indexed in `(row, column)` order, so the code
reads each location as:

```python
pixel = image[y - 1, x - 1]
```

This is covered by tests because reversing the pair lands in background or
missing image lines for these products.

## Commands

```powershell
.\run.ps1 init
.\run.ps1 download
.\run.ps1 analyze
.\run.ps1 report
.\run.ps1 all
.\run.ps1 test
.\run.ps1 app
.\run.ps1 detect-all
.\run.ps1 detect -Date 2001-01-13
.\run.ps1 exports
```

## Project Layout

- `jupiter_pipeline.py`: archive, database, image, and reporting pipeline
- `known_events.json`: published ground-truth detections
- `app_server.py` and `web/`: local research workbench
- `detection_pipeline.py`: first-pass bright blob detection and tracking
- `docs/jupiter_lightning_detector_one_page.md`: one-page explanation
- `docs/research_grade_pipeline_plan.md`: science-first pipeline plan
- `docs/research_log_2026-07-02.md`: dated engineering/research log
- `docs/current_results_summary.md`: current processed-date evidence summary
- `docs/reproducibility_checklist.md`: clean-room reproduction steps
- `docs/roadmap.md`: GitHub-facing scientific roadmap
- `data/calibrated`: calibrated I/F images and labels
- `data/metadata`: OPUS metadata snapshots
- `data/previews`: archive browse images
- `outputs/detection`: candidates, summaries, contact sheets, and labels

## Current Results Snapshot

As of the July 2, 2026 export run:

- Processed dates: 2000-12-31, 2001-01-01, 2001-01-04, 2001-01-05,
  2001-01-08, 2001-01-09, 2001-01-10, 2001-01-11, 2001-01-13.
- Images processed: 221 Cassini ISS NAC/H-alpha frames.
- Raw bright regions saved: 196,233.
- Review candidates after artifact filters: 12,611.
- Published lightning marks recovered: 6 of 6.
- Scientific review queue rows: 106.

This is not a discovery claim. The expanded dataset increases the review pool
and gives stronger validation artifacts, but unmatched candidates still need
manual review plus temporal/geometric checks.

## Sensitivity / Threshold Sweep

`.\run.ps1 exports` also writes `outputs/detection/threshold_sweep.csv`. This
does not claim a better detector by itself. It answers a practical review
question: if the SNR threshold or minimum blob size is made stricter, how many
candidates remain and how many published detections are still recovered?

That table is useful for explaining false positives because it shows the cost of
stricter rules. A stricter detector may reduce review workload, but it can also
start missing real published detections.

## Review Evidence Exports

`.\run.ps1 exports` also writes:

- `known_match_report.csv`: nearest detector candidate to every published mark,
  including pixel offset and whether it is recovered within 8 pixels.
- `scientific_review_queue.csv`: curated rows for published matches, top
  unmatched temporal tracks, strong single-frame candidates, and likely
  artifacts.
- `temporal_track_summary.csv`: candidate tracks across frames with start/end
  image, net motion, median brightness, score, and linked candidate IDs.
- `review_packet.md`: a plain-English summary of the current evidence, safe
  claims, date counts, known-match table, and strongest temporal tracks.
- `review_artifacts/*.png`: contact sheets for published matches, unmatched
  temporal tracks, likely artifacts, and strong single-frame candidates.

These files are designed for research review. They make the detector behavior
auditable instead of asking someone to trust a dashboard.

## Next Scientific Feature

The current detector works in x/y pixels. Future validation should map
candidates to Jupiter latitude and longitude. If the same storm appears at the
same planet location across multiple frames or days, that is stronger evidence
than a single bright spot.

The next publishable-analysis path is to connect credible H-alpha candidates to
nearby broadband/filter images. That is what would make color or spectrum work
possible instead of just claiming a detector works.

## Sources

- OPUS API guide: <https://opus.pds-rings.seti.org/apiguide.pdf>
- OPUS archive: <https://opus.pds-rings.seti.org/>
- OPUS Jupiter search example: <https://opus.pds-rings.seti.org/#/COISScamera=Narrow+Angle&instrument=Cassini+ISS&planet=Jupiter&qtype-SURFACEGEOjupiter_limbaltitude=any&unit-SURFACEGEOjupiter_limbaltitude=km&SURFACEGEOjupiter_planetographiclatitude1=-87&SURFACEGEOjupiter_planetographiclatitude2=88&qtype-SURFACEGEOjupiter_planetographiclatitude=any&unit-SURFACEGEOjupiter_planetographiclatitude=degrees&surfacegeometrytargetname=Jupiter&time1=2001-01-01T01:43:11.699&qtype-time=any&unit-time=ymdhms&cols=opusid,instrument,planet,target,time1,observationduration&widgets=SURFACEGEOjupiter_limbaltitude,SURFACEGEOjupiter_planetographiclatitude,surfacegeometrytargetname,time,planet,COISScamera,instrument&order=time1,opusid&view=browse&browse=gallery&cart_browse=gallery&startobs=29&cart_startobs=1&detail=co-iss-n1359382963>
- Dyudina et al. (2004), Icarus 172, 24-36:
  <https://ui.adsabs.harvard.edu/abs/2004Icar..172...24D/abstract>
- Local copy of the published paper, if present:
  `C:\Users\vedar\Downloads\lightning_cassini_published.pdf`
