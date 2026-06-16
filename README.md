# Cassini Jupiter Lightning Workflow

This project reproduces the published Cassini ISS detections of lightning on
Jupiter and provides a foundation for cataloging and screening additional
images from the OPUS archive.

The initial ground-truth set comes from Dyudina et al. (2004), *Lightning on
Jupiter observed in the H-alpha line by the Cassini imaging science
subsystem*. It contains six detections in three Cassini NAC/HAL images.

## Quick start

From PowerShell:

```powershell
.\run.ps1 all
```

The command:

1. Creates `jupiter_lightning.sqlite`.
2. Retrieves OPUS metadata and calibrated VICAR/PDS products if missing.
3. Reads the calibrated 1024 x 1024 I/F arrays.
4. Measures the published lightning locations against local backgrounds.
5. Generates enhanced full frames, annotated crops, CSV exports, and a report.

Launch the interactive local workbench:

```powershell
.\run.ps1 app
.\run.ps1 detect
```

The app opens at `http://127.0.0.1:8765`. It provides:

- original versus calibrated/processed image comparison
- output resizing to 75%, 50%, or 25%
- 512, 256, and 128 pixel inspection crops
- black point, white point, and midtone controls
- click-to-place Cassini image coordinates
- local candidate classifications and research notes
- processed PNG export
- browser-local IndexedDB image library and processing history
- portable JSON library backup/import
- storage quota monitoring with a backup warning before the browser fills

Uploaded PNG, JPEG, WebP, and BMP images are processed locally in the browser.
They are not sent to OPUS or another external service.

The static meeting report remains at `outputs/report.html`.

## Important coordinate convention

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
```

## Project layout

- `jupiter_pipeline.py`: archive, database, image, and reporting pipeline
- `known_events.json`: published ground-truth detections
- `meeting_walkthrough.ipynb`: concise notebook for the research meeting
- `app_server.py` and `web/`: local research workbench
- `detection_pipeline.py`: first-pass bright blob detection and tracking
- `start_workbench.ps1`: desktop-launch entry point
- `data/calibrated`: calibrated I/F images and labels
- `data/metadata`: OPUS metadata snapshots
- `data/previews`: archive browse images
- `outputs`: figures, measurements, and HTML report

## Scientific scope

This first milestone verifies data access, calibration-product ingestion, and
reproduction of known detections. It does not yet claim a new lightning
detection. A defensible new-event search should add image navigation and
temporal registration so repeated features can be tested against Jupiter's
rotation; single bright pixels alone remain cosmic-ray candidates.

## First Detection Milestone

Run:

```powershell
.\run.ps1 detect
```

This queries the 23 Cassini ISS NAC/HAL Jupiter frames from January 1, 2001,
downloads calibrated products if missing, performs high-pass enhancement,
detects connected bright regions, links nearby detections across adjacent
frames, and writes:

- `outputs/detection/candidates.csv`
- `outputs/detection/summary.json`
- `outputs/detection/candidate_contact_sheet.png`

This is an explainable first-pass candidate finder. It is meant to generate
review targets, not final lightning claims.

## Sources

- OPUS API guide: <https://opus.pds-rings.seti.org/apiguide.pdf>
- OPUS archive: <https://opus.pds-rings.seti.org/>
- Dyudina et al. (2004), Icarus 172, 24-36
