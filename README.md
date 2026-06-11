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

Open the generated report at:

```text
outputs/report.html
```

The main presentation figure is:

```text
outputs/known_lightning_contact_sheet.png
```

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
```

## Project layout

- `jupiter_pipeline.py`: archive, database, image, and reporting pipeline
- `known_events.json`: published ground-truth detections
- `meeting_walkthrough.ipynb`: concise notebook for the research meeting
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

## Sources

- OPUS API guide: <https://opus.pds-rings.seti.org/apiguide.pdf>
- OPUS archive: <https://opus.pds-rings.seti.org/>
- Dyudina et al. (2004), Icarus 172, 24-36

