---
name: Candidate review
about: Review a detector candidate or candidate track
title: "Review candidate: "
labels: candidate-review
assignees: ""
---

## Candidate

- Candidate ID:
- Image ID:
- Date:
- x/y:
- Review category:
- Review batch:
- Crop or workbench link:

## Initial Detector Measurements

- SNR:
- Blob size:
- Candidate score:
- Artifact flags:
- Track length, if any:

## Human Label

Choose one:

- [ ] known-lightning
- [ ] possible-lightning
- [ ] artifact
- [ ] cosmic-ray-hot-pixel
- [ ] uncertain

Confidence:

- [ ] low
- [ ] medium
- [ ] high

## Evidence Notes

What do you see in the thumbnail or source image?

Does it repeat in nearby frames?

Does it look diffuse, single-pixel, streak-like, edge-related, or noise-like?

## Evidence Checked

- [ ] Original image context
- [ ] Contrast-stretched crop
- [ ] Nearby frames / temporal persistence
- [ ] Artifact flags
- [ ] Published lightning comparison
- [ ] Nearby filter context

## Second Review

- [ ] Needs second review
- [ ] Second review completed

## Follow-Up

- [ ] Ready to export into labels CSV
- [ ] Needs geometry check
- [ ] Needs nearby-filter/color check
