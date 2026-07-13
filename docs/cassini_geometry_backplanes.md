# Cassini candidate geometry and backplanes

The detector measures candidates in image coordinates first: sample `x` and
line `y`. Scientific comparison across frames needs a second step that maps each
pixel to a point on Jupiter.

This repository uses the USGS ISIS Cassini ISS camera model for that mapping:

```text
PDS calibrated IMG + detached LBL
  -> ciss2isis
  -> spiceinit
  -> campt(sample, line)
  -> Jupiter latitude/longitude
```

`candidate_backplanes.py` implements the batch runner. It groups candidate rows
by image, creates one ISIS cube per image, attaches the appropriate SPICE
geometry, queries all candidate pixels, and writes:

```text
outputs/detection/candidate_geometry.csv
outputs/detection/geometry_run_status.json
```

Coordinate conventions are explicit in the output. Latitude is
planetographic when ISIS supplies it. Longitude is stored as positive-west,
0-360 degrees. The public review interface must not treat image-level OPUS
center geometry as candidate coordinates.

## Run in an ISIS environment

Install USGS ISIS and its data area in Linux, WSL, a container, or the
Andromeda research environment. The commands `ciss2isis`, `spiceinit`, and
`campt` must be available.

```bash
python candidate_backplanes.py --check
python candidate_backplanes.py --tolerance 1.0
python build_public_site_data.py
```

ISIS downloads the mission kernels it needs through its data management
workflow. The complete Cassini NAIF archive is very large, so use the smallest
time-covered kernel/data subset appropriate for the 2000-2001 observations.

## Validation gate

Coordinates are not ready for scientific claims merely because the program
runs. First compare the projected positions for the six published lightning
marks with the paper's reported locations and inspect limb/no-surface failures.
Only after that check should the one-degree grouping control be used as evidence
that candidates occupy the same Jovian location across frames.

Official references:

- USGS ISIS `ciss2isis`: https://isis.astrogeology.usgs.gov/9.0.0/Application/presentation/Tabbed/ciss2isis/ciss2isis.html
- USGS ISIS `campt`: https://isis.astrogeology.usgs.gov/9.0.0/Application/presentation/Tabbed/campt/campt.html
- NAIF Cassini SPICE archive: https://naif.jpl.nasa.gov/pub/naif/pds/data/co-s_j_e_v-spice-6-v1.0/cosp_1000/aareadme.htm
