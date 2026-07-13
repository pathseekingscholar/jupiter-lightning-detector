# Geometry Input Inventory

This inventory checks whether the local project has the inputs needed to convert detector x/y pixels into Jupiter latitude/longitude. It does not perform that projection.

## Summary

- Images inventoried: 221
- Projection-input-ready images: 0
- Blocked images: 221

## Blocking Inputs

| Blocker | Images |
|---|---:|
| `missing_documented_iss_camera_model` | 221 |
| `missing_local_spice_kernels` | 221 |

## What Is Present

- Calibrated PDS image and label products exist for the processed frames.
- PDS labels provide timing, spacecraft clock counts, instrument ID, filter name, image dimensions, and exposure metadata.
- OPUS metadata provides image-level viewing geometry such as subobserver/subsolar longitude, range, phase, incidence, emission, and center resolution.

## What Is Missing

- A documented Cassini ISS camera model usable for pixel-to-ray projection.
- Local SPICE kernels for spacecraft trajectory, pointing, frame definitions, leapseconds, and spacecraft clock conversion.

## Safe Interpretation

The project has enough local metadata to explain why candidate geometry is blocked, but not enough to claim candidate latitude/longitude. The next implementation step is to collect/document camera and SPICE inputs, then project a small validation set before applying geometry to all candidates.