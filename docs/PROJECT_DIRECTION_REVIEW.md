# Project direction review

Reviewed September 5, 2026 against `main` at
[`7bd72cd63ac23575ab5d92985fce35ad369a89e8`](https://github.com/niederee/landscape/tree/7bd72cd63ac23575ab5d92985fce35ad369a89e8).
The checkout was clean before implementation. Findings below describe that
baseline; changes and their verification belong in `PROJECT_PROGRESS.md`.

## Assessment

**Yes: this is a sound project for producing traceable residential landscape
master plans and managing a multiyear improvement program.** Structured geometry,
explicit sources, quantities, and reproducible drawings are a useful foundation.
The strongest near-term result is a plan the homeowner and a designer can review
together, revise, compare, and phase.

The current software is an existing-conditions inventory and vector drawing tool.
It does not yet produce a landscape design, a multiyear plan, or a construction
drawing set. Professional presentation and trustworthy site/design content are
separate requirements. The original specification already makes this distinction;
preserve it rather than promise that software validation certifies a site.

The direction change is primarily **delivery priority**: finish a useful portable
review file and capture the actual property, then build the smallest concept and
phase workflow needed to make a real decision. Keep the Python geometry core and
YAML files. Avoid expanding the report-schema infrastructure as the next product
milestone when the real base plan is still absent.

## Baseline evidence

| Capability | Actual state and evidence |
|---|---|
| Source models | `model/project.py` models parcel, structures/doors, hardscape, lines, trees, beds, lawn, utilities, and reference metadata. Schema 1 uses local feet. |
| Loading | `io/yaml_loader.py` supports one YAML file or a directory with optional `existing_conditions.yaml` and `references.yaml`. No concept/program/phase loader exists. |
| Geometry | `model/geometry.py` wraps Shapely Point, LineString, and simple Polygon. Polygon holes and MultiPolygon are not supported inputs. |
| Validation | `analysis/validation.py` checks polygon validity/containment, IDs, declared sources, tree placement, hardscape overlaps, and utility clearances. Missing reference files are warnings; `validate --strict` makes warnings fail. |
| Quantities and review data | `estimating/quantities.py`, `inspection.py`, and `analysis/reporting.py` provide existing-condition metrics, inspection, reports, and exports. They are reusable inputs to HTML. |
| Drawing | `rendering/svg.py` produces one 17-by-11-inch SVG sheet with fitted geometry, semantic layer groups, labels, tree and utility symbols, and a graphic scale. No HTML, PDF, or DXF renderer exists at this revision. |
| Planning | `LandscapeProject` has no program, analysis overlays, concepts, master plan, phases, costs, or planting schedule. A `status` or `phase` field on some entities does not implement these workflows. |
| Real property | `projects/greenleaf` has one estimated rectangular parcel, one estimated house footprint, and one pending survey record. No actual survey file, photos, trees, beds, hardscape, or utilities are present. |
| Verification | On the unchanged baseline, Python 3.13.3: `.venv/bin/python -m pytest -q` returned **62 passed**. `.venv/bin/python -m landscape_planner.cli.main validate projects/greenleaf` returned **0 errors, 1 missing-survey warning**, exit 0. These establish software behavior, not physical accuracy. |

The baseline `PROJECT_PROGRESS.md` mixes historical test runs, proposed checks,
and old branch statuses. Its next step is strict-mode documentation. Replace that
active priority with the outcomes below and keep a short current verification
record. Do not infer that every historical command was rerun in this review.

## Drawing and validation gaps to address

These are baseline source-code findings, not claims about the new branch:

- The north arrow ignores `north_rotation_degrees`. It is emitted before an opaque
  title block occupying its location, so sheet painting order hides it. Correct
  orientation and visible annotations are prerequisites for a trustworthy viewer.
- The parcel has no selectable SVG entity ID. Doors are inspectable but not drawn.
  Layer selection must associate geometry and labels and clearly explain any
  entity without a drawn representation.
- Validation's `_iter_entities` excludes doors, although inspection includes them.
  Door duplicate IDs and broken source references can therefore escape validation.
- Linear features accept any `GeometryData`; validation does not require a
  LineString, but the SVG renderer does. Reject unsupported shapes before export.
- The fitted sheet is not a selectable architectural drawing scale. No dimension
  system, label collision layout, planting schedule, or complete construction
  legend exists. Some text can exceed the fixed title-block width. Keep browser
  printing labeled as review output and verify the graphic scale on fixed sheets.
- Easements/setbacks can be stored but are not rendered or enforced by current
  validation. Optional provenance and a passing check do not establish completeness.

Fix demonstrated H1 prerequisites in the implementation; retain remaining gaps
as explicit follow-up work. Do not broaden the PR into every planned subsystem.

## Prioritized outcome roadmap

| Priority | Deliverable | Acceptance outcome |
|---|---|---|
| H1, now | Standalone single-plan HTML using existing SVG and core metrics; see ADR 0004 | A copied file opens offline through `file://`, with layers, navigation, linked inspection, source status, warnings, and a static fallback. Synthetic hostile/private fixtures and existing regressions pass. Record browsers actually tested. |
| Site capture, alongside H1 | Replace Greenleaf placeholders from supplied survey and field observations | Owner can reconcile parcel, footprint, access, hardscape, trees, and services against source documents and independent measurements. Missing information remains explicit. |
| Next design slice | Homeowner program plus manually observed shade, privacy, drainage, and circulation notes | One concrete priority can be discussed against the captured site. No simulated environmental score is required. Add structured overlay models only for the selected use case. |
| H2 | Core concept operations and two deliberately different authored alternatives, then HTML comparison | Immutable baseline; add/update/remove/preserve operations reject invalid references; unchanged geometry stays aligned; quantity differences reconcile with core reports. Owner can explain the tradeoff. |
| H3 | Selected master plan, cumulative phases, itemized ranges and dependencies | Show what exists after each phase, what it changes, and what precedes it. Separate demolition/replacement from net area; expose missing cost sources and avoidable rework. |
| Detailed delivery | Planting schedule and required dimensioned/vector sheets for the selected scope | Design review checks source accuracy, legibility, scale references, quantities, and relevant site constraints before contractors rely on the package. |
| H4, optional | Portable review comments and selected photo callouts | Feedback retains entity/snapshot context and cannot silently modify canonical project files. |

Defer automatic design optimization, full CAD editing, advanced solar simulation,
3D, a national plant database, and a hosted collaboration service until a real
decision demonstrates the need. No new database or JavaScript geometry engine is
needed for these immediate outcomes.

## Greenleaf capture dependency

The 80-by-130-foot parcel is **starter data, not a measurement of Greenleaf**.
The existing survey reference is a placeholder, not evidence of a survey review.
An export must make its provisional source status prominent. Never relabel an
estimate as surveyed merely to satisfy a validation gate.

The next useful homeowner input is the closing survey, followed by a short field
walk and photos. Work from this ordered checklist:

1. Record survey date/reference, boundary dimensions, coordinate origin and north
   convention. Enter geometry in feet; reconcile independent dimensions and any
   discrepancy. Keep the original source separate from generated drawings.
2. Capture house footprint and major exits, driveway/patio/walks, fences and gates,
   existing trees/canopies, beds/lawn, utility equipment and service access.
3. Record observed wet areas, downspouts and drainage direction, afternoon shade,
   privacy problems, and photo locations. Unknown elevations remain unknown.
4. Mark each important entity's source, method, confidence, and known accuracy.
   Track observation dates in source records where supported; do not invent a
   precision from a confidence label. List unmodeled or uncertain features.
5. Confirm desired outdoor uses, maintenance tolerance, approximate annual budget,
   DIY versus contractor scope, and which area should improve first. Use those
   answers to choose the first two alternatives rather than inventing preferences.

Capture real source documents and identifying photographs in an owner-controlled
project location. This public repository can carry synthetic demonstrations and
the generic workflow without requiring publication of the homeowner's survey.

## Specification integration

This review supplies the repository evidence missing from the original
`LANDSCAPE_STANDALONE_HTML_SPEC.md`. Its historical access limitation should not be
mistaken for the current review status. Adopt that addendum's H1 direction through
[ADR 0004](adr/0004-standalone-review-export.md); it changes output priority and
permits read-only interaction under the original specification's no-editor rule.
It does not declare all H1 gates passed or change the source schema. Consult the
current progress record for implementation results and remaining release gates.
