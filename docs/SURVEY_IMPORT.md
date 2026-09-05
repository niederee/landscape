# Importing transcribed survey courses

The survey command converts explicitly supplied bearings and distances into a
candidate property boundary in local feet. It does not infer dimensions from an
image. Transcribe every course in order from a legible survey and retain its source
reference. Review ambiguous characters against the original document before use.

The following fixture is **synthetic**, not a reconstruction of Greenleaf:

```yaml
schema_version: 1
source: Synthetic rotated rectangle for workflow testing
origin: [0, 0]
max_closure_error_ft: 0.1
legs:
  - {bearing: 'N 30 E', distance_ft: 100}
  - {bearing: 'S 60 E', distance_ft: 50}
  - {bearing: 'S 30 W', distance_ft: 100}
  - {bearing: 'N 60 W', distance_ft: 50}
```

Save it as `traverse.yaml` and run:

```bash
landscape survey traverse.yaml --output traverse-report.json
```

The JSON report preserves the supplied traverse and contains `accepted`,
`boundary`, `closure_dx_ft`, `closure_dy_ft`, `closure_error_ft`, `closure_ratio`,
`perimeter_ft`, and `diagnostics`. A rejected traverse produces no boundary. The
command returns a nonzero exit status when reconstruction is rejected. Invalid
bearings or nonfinite measurements are input errors.

Coordinates have positive x east and positive y north. The origin is an arbitrary
local coordinate, not a geographic location. Bearings support decimal quadrant
angles (`N21.5W`), degrees/minutes/seconds (`N21°30'00"W` or `N 21 30 00 W`), and
the cardinal directions `N`, `E`, `S`, `W`. Quadrant angles must be in [0, 90];
minutes and seconds must be below 60. Distances are positive finite feet. At least
three courses are required.

`closure_dx_ft` and `closure_dy_ft` describe the final endpoint minus the origin.
`closure_error_ft` is the length of that vector. `closure_ratio` is this error
divided by the sum of supplied distances, **not** the reciprocal 1:N convention.
`perimeter_ft` sums supplied courses and excludes the residual closing segment.
No course is balanced, shortened, or redistributed to make a traverse close. If
the residual gap fits the explicit tolerance, the ring retains the last endpoint
and adds a segment back to the origin. That segment can be very short. Polygon
self-intersections and zero area are rejected even when closure passes.

An accepted result means only that this mathematical reconstruction passed these
checks. Closure cannot establish that transcribed courses are correct, that a
survey reflects current conditions, or that proposed work meets requirements.

Review the reconstructed orientation and every edge against the survey before
copying `boundary` into a project's boundary geometry. Retain source metadata and
provisional confidence for manual transcription. Keep actual fence alignments,
recorded easements, and supplied pool exclusion constraints as distinct features;
fences do not redefine property lines. Dimensions or offsets specific to pools
should not silently prohibit planting or all landscape work.

For Python callers:

```python
from landscape_planner.surveying import load_traverse, reconstruct_traverse

result = reconstruct_traverse(load_traverse("traverse.yaml"))
report_json = result.model_dump_json(indent=2)
if result.accepted:
    candidate_boundary = result.boundary
```

Keep real residential surveys, identifying source paths, and reconstructed private
property geometry out of public example fixtures unless the owner explicitly
authorizes publication. Synthetic fixtures are sufficient to test the importer.
