# Cassini candidate geometry and backplanes

The detector measures candidates in image coordinates first: sample `x` and line `y`. Scientific comparison across
frames needs a second step that maps each pixel to a point on Jupiter.

This repository uses the USGS ISIS Cassini ISS camera model:

```text
raw PDS EDR IMG + detached LBL
  -> ciss2isis
  -> spiceinit web=true
  -> campt(sample, line)
  -> Jupiter latitude/longitude
```

`candidate_backplanes.py` groups review rows by image, creates one ISIS cube per image, attaches SPICE geometry, queries
all candidate pixels, and writes:

```text
outputs/detection/candidate_geometry.csv
outputs/detection/geometry_run_status.json
```

Latitude is planetographic when ISIS supplies it. Longitude is positive west from 0 to 360 degrees. Image-level OPUS
center geometry is never substituted for candidate coordinates.

## Local setup

The repository includes a Docker build pinned to USGS ISIS 10.0.0. Docker is used only for local geometry processing;
it is not part of the public reviewer.

```powershell
.\run.ps1 geometry-runtime
.\run.ps1 geometry-data
.\run.ps1 geometry-check
.\run.ps1 geometry-project
.\run.ps1 public-site-data
```

`geometry-data` downloads the small Cassini import table and only the shared base camera files needed here.
`spiceinit web=true` retrieves observation-specific SPICE records. Raw EDR products are downloaded from OPUS on demand
for camera initialization; detector measurements continue to use calibrated CISSCAL products.

## Validation gate

Coordinates are not ready for scientific claims merely because the program runs. First project the six published
lightning marks and inspect limb or no-surface failures. The paper supplies image x/y references, not a latitude and
longitude table, so this is an intersection and consistency check rather than comparison to published surface
coordinates. After that check, the configurable one-degree grouping can identify candidates at nearby Jovian locations.

Official references:

- USGS ISIS installation: https://astrogeology.usgs.gov/docs/how-to-guides/environment-setup-and-maintenance/installing-isis-via-anaconda/
- USGS ISIS data area: https://astrogeology.usgs.gov/docs/how-to-guides/environment-setup-and-maintenance/isis-data-area/
- USGS ISIS `ciss2isis`: https://isis.astrogeology.usgs.gov/dev/Application/presentation/Tabbed/ciss2isis/ciss2isis.html
- USGS ISIS `campt`: https://isis.astrogeology.usgs.gov/dev/Application/presentation/Tabbed/campt/campt.html
- NAIF Cassini SPICE archive: https://naif.jpl.nasa.gov/pub/naif/pds/data/co-s_j_e_v-spice-6-v1.0/cosp_1000/aareadme.htm
