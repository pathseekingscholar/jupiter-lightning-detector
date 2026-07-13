# Candidate geometry validation

## Batch result

- Queue rows: 106
- Coordinates computed: 42
- No surface intersections: 64
- Projection failures: 0
- Published matches: 6
- Published matches projected: 6
- Surface groups: 41
- Multi candidate groups: 1
- Multi image groups: 1

## Published-reference candidates

| Label | Image | Paper x/y | Detector x/y | Offset px | Latitude | Longitude W | Status |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | N1357029177 | 731.0, 211.0 | 731.37, 212.49 | 1.54 | 26.536009586308 | 162.63407247623 | computed |
| 2 | N1357029177 | 846.0, 397.0 | 847.00, 402.23 | 5.32 | 38.196773110058 | 165.06651001994 | computed |
| 3 | N1357810970 | 955.0, 357.0 | 955.53, 354.96 | 2.11 | -14.786886519008 | 83.221744288524 | computed |
| 3* | N1357810970 | 951.0, 330.0 | 951.80, 333.08 | 3.18 | -16.499649132725 | 82.459280800579 | computed |
| 4 | N1357885387 | 775.0, 341.0 | 769.65, 339.50 | 5.56 | -15.147007998117 | 79.797369884111 | computed |
| 4* | N1357885387 | 775.0, 316.0 | 776.00, 318.00 | 2.24 | -16.949636851636 | 79.916211844964 | computed |

The paper validates image-pixel recovery. It does not provide a latitude/longitude table for these six marks. The surface coordinates above are new derived metadata from the ISIS camera model and must retain their method and coordinate-convention fields.

A shared one-degree surface group is a review aid, not proof that candidates are the same storm.
