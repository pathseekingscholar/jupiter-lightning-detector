# Contributing

This project is a research pipeline, so contributions should improve
reproducibility, validation, or scientific review.

## Good Contributions

- Improve OPUS/PDS provenance tracking.
- Add stronger artifact rejection tests.
- Improve temporal track validation.
- Add geometry mapping from image pixels to Jupiter coordinates.
- Add human-review labels with short reasons.
- Improve documentation that helps another researcher reproduce the run.

## Labeling Candidates

Candidate labels should use the project label set:

- `known-lightning`
- `possible-lightning`
- `artifact`
- `cosmic-ray-hot-pixel`
- `uncertain`

Every label should include a short reason. Do not delete false positives; they
are useful negative examples.

## Scientific Claims

Do not claim new lightning unless the candidate survives:

- manual review,
- temporal consistency checks,
- artifact rejection,
- and, when possible, geometry or nearby-filter validation.

## Generated Data

Large local outputs are intentionally ignored by Git:

- `data/`
- `outputs/`
- SQLite files
- extracted paper text

Regenerate them with:

```powershell
.\run.ps1 coverage
.\run.ps1 detect-all
.\run.ps1 exports
```
