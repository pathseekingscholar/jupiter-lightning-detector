# Geometry Acquisition Checklist

This checklist lists the camera and SPICE inputs needed before candidate x/y pixels can be projected to Jupiter latitude/longitude. It does not download kernels and it does not perform projection.

## Official Sources

- NAIF Cassini kernels root: https://naif.jpl.nasa.gov/pub/naif/CASSINI/kernels/
- NAIF/PDS Cassini SPICE archive readme: https://naif.jpl.nasa.gov/pub/naif/pds/data/co-s_j_e_v-spice-6-v1.0/cosp_1000/aareadme.htm
- Cassini ISS instrument kernel example: https://naif.jpl.nasa.gov/pub/naif/CASSINI/kernels/ik/release.10/cas_iss_v09.ti

## Summary

- Required input groups: 7
- Present locally: 0
- Missing locally: 7

## Required Inputs

| Input | Kind | Status | Local matches | Required for |
|---|---|---|---:|---|
| `iss_camera_model` | `IK` | `missing` | 0 | pixel_to_camera_ray |
| `cassini_frames` | `FK` | `missing` | 0 | camera_frame_to_spacecraft_frame |
| `cassini_pointing` | `CK` | `missing` | 0 | spacecraft_pointing_at_image_time |
| `cassini_trajectory` | `SPK` | `missing` | 0 | spacecraft_and_jupiter_position |
| `spacecraft_clock` | `SCLK` | `missing` | 0 | image_sclk_to_et |
| `leapseconds` | `LSK` | `missing` | 0 | utc_to_et |
| `jupiter_body_model` | `PCK` | `missing` | 0 | ray_jupiter_intercept |

## Acquisition Notes

- Keep downloaded kernels out of Git unless a tiny text kernel is explicitly approved for source control.
- Record every downloaded file in this checklist or a future metakernel before running projection code.
- Coverage must be checked against the image times in `outputs/detection/geometry_input_inventory.csv`.
- The first projection test should use the six published validation candidates before applying geometry to unmatched candidates.

## Safe Interpretation

When this checklist is mostly missing, candidate-level geometry is not ready. The detector can still work in image coordinates, but it cannot make storm-location claims on Jupiter.