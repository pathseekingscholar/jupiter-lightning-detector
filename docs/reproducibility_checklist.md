# Reproducibility Checklist

This checklist is for rebuilding the current detector outputs from the public
code plus OPUS/PDS data access.

## Environment

- Windows PowerShell or a shell that can run Python 3.
- Python packages used by the repo, especially NumPy and Pillow.
- Network access to OPUS / PDS Ring-Moon Systems Node.

The local `run.ps1` script prefers the bundled Codex Python runtime when
available, then falls back to `py` or `python`.

## Rebuild Steps

```powershell
.\run.ps1 all
.\run.ps1 detect-all
.\run.ps1 exports
.\run.ps1 test
.\run.ps1 app
```

Expected local app:

```text
http://127.0.0.1:8765
```

## Local Generated Files

These are intentionally not tracked in Git:

- `data/`
- `outputs/`
- `jupiter_lightning.sqlite`
- extracted paper text
- generated HTML reports

The outputs are reproducible local products, not source files.

## Main Evidence Files

After `.\run.ps1 exports`, inspect:

- `outputs/detection/dataset_manifest.csv`
- `outputs/detection/detection_summary.csv`
- `outputs/detection/known_match_report.csv`
- `outputs/detection/scientific_review_queue.csv`
- `outputs/detection/temporal_track_summary.csv`
- `outputs/detection/threshold_sweep.csv`
- `outputs/detection/review_packet.md`
- `outputs/detection/review_artifacts/*.png`

## Expected Validation Result

The current validation should recover 6 of 6 published lightning marks from
Dyudina et al. (2004), Table 2, within an 8-pixel matching radius.

## Non-Claims

- The detector has not confirmed new lightning.
- The candidate score is not a calibrated probability.
- YOLO is not used in the current detector.
- Unmatched candidates are not automatically false and not automatically real.
