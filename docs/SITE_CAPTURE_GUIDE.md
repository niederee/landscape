# Capture the site before designing it

The checked-in Greenleaf parcel and house are placeholders. Neither their
dimensions nor their position describe a verified property. Keep that example
unchanged until the owner supplies actual evidence; a successful validation
command only checks the supplied model.

## Start with a private working project

Copy the starter project into an owner-controlled directory **outside this public
repository**. Keep original surveys, proposals and photographs there. The
repository's ignore rules exclude generated outputs; they do not automatically
exclude source PDFs, photographs, or identifying YAML. An HTML privacy profile
does not protect files committed to Git.

Use separate folders for the original sources and working notes. Keep original
documents intact, including dates and revision information. For any later public
example, use deliberately synthetic data. Do not replace real coordinates with
plausible invented coordinates and continue calling it the owner's plan.

The loader accepts `project.yaml`, `references.yaml` and
`existing_conditions.yaml` in the same directory. Reference filenames are
relative to the project directory. Register sources in `references.yaml`; point
an entity's `source.reference` at its stable reference ID. The application tracks
these documents but does not extract geometry from a PDF or photograph.

## First packet to collect

| Input | What to supply | What it enables |
|---|---|---|
| Closing survey or other authoritative boundary source | Complete original document, date, revision and any relevant legend | Boundary interpretation, house placement and documented constraints |
| Site overview | Photos of each outdoor area plus a sketch identifying where each photo was taken | Inventory and visible conflicts |
| Current use and priorities | Desired activities, what prevents them today, first area to improve | Two meaningful design alternatives |
| Spending and effort | Approximate first-year and later-year budget ranges, maintenance tolerance, DIY/contractor preference | Realistic scope and sequencing |
| Known constraints | Documents or observations for access, utilities, drainage, easements and approvals; list what is still unknown | Targeted follow-up instead of assumed constraints |

A partial packet is useful. Label missing items explicitly. Do not delay the
software demonstration for missing site data, but do not present its synthetic
alternatives as proposals for the real yard.

## Establish a repeatable coordinate frame

1. Choose a fixed, identifiable origin from the source plan and describe it in
   `coordinate_system.origin_description`. Keep the same origin for all captures
   and alternatives.
2. Record local X and Y directions on the sketch. Enter horizontal dimensions in
   feet and areas in square feet; convert inches explicitly. Preserve the
   original dimension alongside converted working values when useful.
3. Set `north_rotation_degrees` to the clockwise angle from local +Y to north.
   This rotates the north arrow, not the authoritative geometry. Do not rotate
   coordinates a second time to compensate for the drawing.
4. Reconstruct the boundary from the supplied source. Do not infer legal lines
   from a fence, aerial image or the starter rectangle. If source interpretation
   is unresolved, leave the issue in the capture log for review.
5. Check independent dimensions: overall extents, a diagonal or second offset,
   and house-to-boundary relationships. Record discrepancies instead of stretching
   geometry merely to close a polygon. Boundary reconciliation may need a surveyor.

Confidence is an assessment, not a numeric tolerance. Leave
`estimated_accuracy_ft` unset unless the method supports an estimate. A digitized
survey is not automatically accurate to the last decimal in its coordinates.

## Walk and measure the existing features

Use stable IDs such as `HOUSE001`, `GATE001` and `TREE001` throughout the sketch,
photos and YAML. Record the date, method and source for each capture session.

| Feature | Capture | Do not infer |
|---|---|---|
| House and other structures | Footprint corners and offsets, major exits, steps and obstructions | Unmeasured floor elevations or invisible foundations |
| Patio, drive, walks and decks | Perimeter, material, condition, relevant width changes | Thickness or construction assembly from an overhead photo |
| Fences and gates | Endpoints, gate location/opening width, observed access limits | Property ownership from physical fence position |
| Trees | Trunk position, approximate canopy extent, known species and visible condition | Species certainty, mature size or structural health from a guess |
| Beds and lawn | Existing boundaries, observed plant/soil condition and irrigation | Exact plant counts or soil characteristics that were not observed |
| Utilities and equipment | Visible equipment, recorded routes, required access from a named source | Buried routes, depths or safe clearance dimensions from appearance |

Do not investigate buried utilities by digging for this inventory. Record missing
locations for the appropriate utility/source review before excavation planning.
No universal utility clearance is assumed by the software.

Current input geometry supports points, line strings and simple polygons; a
complex area may need separately identified pieces. Preserve one real entity ID
across alternatives when it is the same retained feature. Keep missing items in
the capture log rather than encoding a fabricated point at `[0, 0]`.

## Record observations separately from conclusions

Photograph drainage after actual rain when possible; note the date and conditions,
wet areas, downspouts and visible flow paths. Unknown grades and elevations remain
unknown. Observe shade at useful times of day, recording time, date and viewing
position; one afternoon is not a seasonal solar study. Describe privacy problems
from the places people use, and note circulation routes, carrying access and
maintenance access.

Attach these observations to entity `notes` or a private capture log. Do not add
unsupported YAML keys to the strict project schema. A photo can have `filename`,
`date`, optional `camera_location` and optional `direction_degrees`; omit camera
coordinates or direction when unknown. Use descriptive photo notes if a bearing
convention has not been established. Photographs are evidence, not calibrated
measurements by default.

Use this table in the private log:

| Item / entity ID | Observation or missing fact | Source and date | Confidence / method | Next action / owner |
|---|---|---|---|---|
| Boundary | Not yet entered | Survey pending | Unknown | Owner supplies survey |
| Outdoor priorities | Not yet agreed | Owner discussion pending | Unknown | Rank activities and first area |

For HOA or jurisdiction rules, retain the actual document/version and identify
the applicable provision before treating a value as a design constraint. The
project does not verify local rules, and this guide supplies no local setbacks,
permit requirements or engineering conclusions.

## Review the captured model

From the software checkout, substitute the private project directory below:

```bash
uv run landscape validate /path/to/private-project
uv run landscape list-entities /path/to/private-project
uv run landscape inspect /path/to/private-project HOUSE001
uv run landscape render /path/to/private-project --format html --profile private
uv run landscape validate /path/to/private-project --strict
```

Resolve errors. Read warnings before deciding whether a conceptual review can
proceed; `--strict` intentionally fails on warnings, including missing source
assets. Do not suppress a missing-survey warning by claiming an estimate is a
survey. Compare the drawing and inspector with the original evidence, check
orientation and independent dimensions, and list anything not represented.

`--profile private` includes identifying project metadata, notes and source
references. `--profile share` omits selected metadata and source assets, but still
contains geometry and entity names/IDs. Review the actual file before sharing;
it is not anonymous. Neither profile embeds the original photographs or survey.

The existing-conditions viewer does not draw doors, easements, setbacks or
rights-of-way. Their absence from a picture is not evidence that the area is
unconstrained. Browser printing is a review convenience, not a certified scaled
construction drawing.

## Ready for real alternatives when

- Boundary, house and the first improvement area reconcile with the available
  sources and independent measurements, or material discrepancies are explicit.
- Existing access, significant trees, equipment and other affected features are
  captured sufficiently to discuss the proposed scope.
- The owner has ranked desired uses and supplied budget/maintenance preferences.
- Unknown constraints have a named follow-up; choices that depend on them stay
  provisional.

See [Planning workflow](PLANNING_WORKFLOW.md) for the executable synthetic
demonstration and the distinction between completed software and real-site inputs.
