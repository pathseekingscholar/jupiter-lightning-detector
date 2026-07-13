# Candidate Geometry Implementation Plan

This plan turns the current geometry blocker into an implementation checklist. It does not claim candidate latitude/longitude is solved yet.

## Current Candidate Geometry State

- Review candidates planned for geometry: 106
- Candidates with image-level bounds only: 57
- Candidates with frame context only: 49
- Candidates blocked by missing frame geometry: 0

Image-level bounds are useful context, but they are not candidate-level coordinates. A true candidate map requires camera/SPICE projection from pixel x/y to Jupiter.

## Review Batches

| Batch | Candidates |
|---|---:|
| `01_known_validation_positive` | 6 |
| `02_temporal_persistence_check` | 30 |
| `03_negative_artifact_examples` | 20 |
| `04_strong_single_frame_check` | 20 |
| `05_low_priority_hold` | 30 |

## Implementation Steps

| Step | Name | Purpose | Deliverable |
|---:|---|---|---|
| 1 | Collect camera geometry inputs | Identify the files needed for pixel-to-ray projection. | Documented ISS camera model, focal length/pixel scale, image center, and distortion assumptions. |
| 2 | Collect SPICE/navigation inputs | Locate spacecraft position, camera pointing, Jupiter body frame, and time kernels for each image. | Kernel list or documented fallback if exact kernels are unavailable. |
| 3 | Project candidate pixels to Jupiter | Convert detector x/y into a camera ray and intersect it with a Jupiter spheroid. | candidate_geometry.csv with latitude, west longitude, incidence, emission, and projection status. |
| 4 | Validate against OPUS bounds | Check that projected points land within image-level OPUS latitude/longitude ranges when those ranges exist. | geometry_validation_report.md showing pass/fail counts and outliers. |
| 5 | Use geometry for temporal tracks | Test whether repeated candidates move consistently in Jupiter coordinates, not just image pixels. | track_geometry_summary.csv with same-storm plausibility flags. |

## Validation Rules

- Do not use image-level latitude/longitude bounds as candidate coordinates.
- Every projected candidate must include a projection status such as `intersects_jupiter`, `off_limb`, `missing_kernel`, or `projection_failed`.
- Published validation candidates should be projected first because they are the safest geometry sanity check.
- Temporal-track geometry should be judged after projection, not before.

## First Rows To Attempt

| Candidate | Image | Batch | x/y | Readiness | Next step |
|---|---|---|---|---|---|
| `1357029177-0148` | `N1357029177` | `01_known_validation_positive` | 731.37, 212.49 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1357029177-0219` | `N1357029177` | `01_known_validation_positive` | 847.00, 402.23 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1357810970-0228` | `N1357810970` | `01_known_validation_positive` | 951.80, 333.08 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1357810970-0239` | `N1357810970` | `01_known_validation_positive` | 955.53, 354.96 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1357885387-0203` | `N1357885387` | `01_known_validation_positive` | 776.00, 318.00 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1357885387-0218` | `N1357885387` | `01_known_validation_positive` | 769.65, 339.50 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1356990399-0202` | `N1356990399` | `02_temporal_persistence_check` | 402.62, 656.20 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1356976983-0161` | `N1356976983` | `02_temporal_persistence_check` | 62.82, 480.68 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1356990399-0080` | `N1356990399` | `02_temporal_persistence_check` | 900.63, 316.07 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1356985927-0141` | `N1356985927` | `02_temporal_persistence_check` | 730.33, 432.12 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1356985927-0245` | `N1356985927` | `02_temporal_persistence_check` | 612.58, 709.56 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |
| `1356985927-0162` | `N1356985927` | `02_temporal_persistence_check` | 835.23, 498.82 | `frame_context_only` | Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame. |