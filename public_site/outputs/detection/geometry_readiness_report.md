# Geometry Readiness Report

This audit checks whether the processed Cassini images have enough local OPUS geometry metadata to support future candidate latitude/longitude mapping.

## Summary

- Images checked: 221
- Images with image-level viewing geometry context: 221
- Images with OPUS latitude/longitude bounds available locally: 61

## Interpretation

The current detector works in image x/y coordinates. Local OPUS metadata provides useful frame-level context such as subobserver longitude, subsolar longitude, center resolution, phase angle, incidence range, and emission range. However, the candidate-level latitude/longitude fields needed to say where a bright blob sits on Jupiter are not available as direct per-candidate values in the current local outputs.

That means x/y-to-Jupiter mapping is not solved yet. The next scientific step is camera geometry or SPICE-style projection from candidate pixel coordinates to Jupiter coordinates.

## Readiness Buckets

| Bucket | Count |
|---|---:|
| Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. | 160 |
| OPUS image-level latitude/longitude bounds exist, but per-candidate mapping still needs camera geometry. | 61 |

## Sample Rows

| Image | Date | Subobserver lon W | Center resolution km/px | Candidate lat/lon ready | Note |
|---|---|---:|---:|---|---|
| N1356976983 | 2000-12-31 | 44.478 | 59.16949 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356977373 | 2000-12-31 | 48.381 | 59.17279 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356977733 | 2000-12-31 | 51.984 | 59.17584 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356981455 | 2000-12-31 | 89.238 | 59.20797 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356981845 | 2000-12-31 | 93.141 | 59.21139 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356982205 | 2000-12-31 | 96.744 | 59.21457 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356985927 | 2000-12-31 | 133.998 | 59.2479 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356986317 | 2000-12-31 | 137.902 | 59.25145 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356986677 | 2000-12-31 | 141.505 | 59.25474 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356990399 | 2000-12-31 | 178.759 | 59.28928 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356990789 | 2000-12-31 | 182.663 | 59.29296 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1356991149 | 2000-12-31 | 186.266 | 59.29636 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1357008677 | 2001-01-01 | 1.71 | 59.47335 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1357009037 | 2001-01-01 | 5.314 | 59.47722 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1357015011 | 2001-01-01 | 65.112 | 59.54271 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1357015401 | 2001-01-01 | 69.015 | 59.54708 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1357015761 | 2001-01-01 | 72.619 | 59.55111 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1357019483 | 2001-01-01 | 109.875 | 59.5934 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1357019873 | 2001-01-01 | 113.779 | 59.59788 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |
| N1357020233 | 2001-01-01 | 117.383 | 59.60204 | no | Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping. |