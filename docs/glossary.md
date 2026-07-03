# Glossary

## Candidate

A bright region saved by the detector for review. A candidate is not confirmed
lightning.

## Known Lightning

A published lightning location from Dyudina et al. (2004) that is used as a
validation target.

## Possible Lightning

A human-reviewed candidate that looks scientifically interesting but still
needs stronger validation before it can be called a discovery.

## Artifact

A detector hit caused by image defects, processing effects, edges, streaks,
noise, or other non-lightning causes.

## Cosmic Ray / Hot Pixel

A bright point-like event that usually appears in one frame and does not behave
like a diffuse storm.

## False Positive

A detector candidate that a human reviewer later decides is not lightning.

## False Negative

A real or published lightning mark that the detector fails to recover.

## True Positive

A detector candidate that matches a known published lightning mark, or later a
candidate that survives scientific validation.

## Unmatched Candidate

A candidate that does not match the published validation marks. It is not
automatically false, and it is not automatically new lightning.

## Candidate Score

A review-priority score. It is not a calibrated probability.

## SNR

Signal-to-noise ratio. In this project, it means how strongly a bright region
stands out from nearby local background variation.

## Blob Size

The number of connected bright pixels in the candidate region.

## Artifact Flag

A warning that the candidate has suspicious properties, such as being
single-pixel, too small, sharp, or streak-like.

## Temporal Track

A set of candidates linked across nearby frames. It is useful evidence, but it
still needs geometric validation.

## Human-In-The-Loop

The workflow where the detector proposes candidates, a human labels them, and
those labels become training or validation data for future models.

## YOLO

A future object-detection model option. YOLO should not be treated as the main
method until enough reviewed labels exist for training and testing.
