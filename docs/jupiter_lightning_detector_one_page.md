# Jupiter Lightning Detector Workbench

## Start Here

This workbench helps review Cassini ISS images of Jupiter for possible
lightning. It does not confirm lightning by itself. It finds bright candidates,
saves the measurements, and lets a human reviewer label the result.

The scientific objective is to build a validated pipeline that identifies
candidate lightning events, minimizes false detections, and enables discovery
and characterization of previously overlooked lightning in Cassini data.

## Simple Pipeline

```text
Cassini image
-> brighten night side
-> find bright spots
-> remove obvious artifacts
-> save candidates
-> human review
-> possible lightning
```

## What The Detector Measures

- image ID: the Cassini image where the candidate appears
- x/y coordinate: the pixel location in the displayed image
- brightness: how strong the bright spot is above nearby background
- blob size: how many connected bright pixels belong to the spot
- SNR/local contrast: how much the spot stands out from local noise
- artifact flags: warnings such as single pixel, too small, sharp, or streak-like
- candidate score: review priority, not a calibrated probability

## Human Labels

- known lightning: matches a published lightning detection
- possible lightning: worth deeper review
- artifact: reviewed as not lightning
- cosmic ray/hot pixel: likely detector or sensor artifact
- uncertain: not enough evidence yet

## Validation

- True positive: the detector finds known published lightning.
- False negative: the detector misses known published lightning.
- False positive: the detector flags something later reviewed as not lightning.
- Unmatched candidate: not in the paper, not automatically false.

## Scientific Boundary

This is not confirmed lightning. These are candidates for review. The detector
does not claim new lightning automatically.

## Publishable Path

1. Recover the published lightning detections.
2. Measure false positives and false negatives.
3. Review unmatched candidates without discarding them automatically.
4. Validate possible new lightning events.
5. Use the larger candidate set to study frequency, latitude distribution,
   storm persistence, temporal evolution, and color or spectral behavior.

The contribution should be new Jupiter science. Classical computer vision,
YOLO, or another model is only the tool.

## Next Scientific Feature

The current detector works in x/y pixels. Future validation should map
candidates to Jupiter latitude and longitude. A bright spot that repeats at the
same planet location across frames or days is stronger evidence than one bright
spot in one image.

## Sources To Keep Open

- Dyudina et al. (2004), Icarus 172, 24-36:
  <https://ui.adsabs.harvard.edu/abs/2004Icar..172...24D/abstract>
- OPUS Jupiter search example:
  <https://opus.pds-rings.seti.org/>
- Local PDF copy:
  `C:\Users\vedar\Downloads\lightning_cassini_published.pdf`
