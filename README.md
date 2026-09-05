# Landscape Planner

Deterministic residential landscape planning from structured YAML data.

The project follows the workflow in `LANDSCAPE_PLANNER_SPEC.md`: structured
property data is the source of truth, geometry calculations are deterministic,
and generated drawings are reproducible outputs.
Report payload schema migration policy is tracked in
`docs/adr/0002-report-schema-versioning.md`.
Longer-lived schema-bearing artifacts (quantities, references manifests, and similar machine-readable outputs)
are planned under
`docs/adr/0003-schema-versioning-for-future-artifacts.md`.

For the current assessment and delivery priorities, read
[`docs/PROJECT_DIRECTION_REVIEW.md`](docs/PROJECT_DIRECTION_REVIEW.md).
The current product models **existing conditions**; concept generation, phase
resolution, cost estimates, and construction documentation are still planned.
The Greenleaf project contains placeholder geometry, not a measured site plan.

## Portable review file

```bash
uv run landscape render examples/synthetic --format html
uv run landscape render projects/greenleaf --format html --output generated/greenleaf-review.html
```

Open `examples/synthetic/generated/html/L1.0_existing_conditions.html` directly
in a browser. Copying that file alone is sufficient: the drawing, controls,
entity inspection, quantities, and styles are embedded. No server or network is
required. Without JavaScript, the plan and review tables remain readable.
Existing `render` calls still produce SVG by default.

HTML defaults to `--profile share`, which omits project identity/location,
notes, descriptions, reference filenames, and source-reference strings.
Entity IDs and drawing labels remain visible: review them before sharing;
this is metadata filtering, not guaranteed anonymization of a recognizable site.
Use `--profile private` to include private review metadata. Neither profile
embeds source documents or photos. Quantities describe the whole snapshot,
independent of which drawing layers are visible.

This is a read-only existing-conditions review, not a design editor or a
construction-ready plan. Provenance and unknown accuracy remain visible.

Optional browser acceptance tests:

```bash
uv sync --extra dev --extra browser
uv run playwright install chromium
uv run pytest tests/browser
```

## Development

Preferred setup:

```bash
uv sync --extra dev
uv run pytest
uv run landscape --help
```

If `uv` is not installed yet, use a local virtual environment as a temporary
fallback:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/landscape --help
```

## First Demo

Validate and render the synthetic existing-conditions project:

```bash
uv run landscape validate examples/synthetic
uv run landscape references examples/synthetic
uv run landscape list-entities examples/synthetic
uv run landscape report examples/synthetic
uv run landscape report examples/synthetic --format json
uv run landscape report examples/synthetic --format csv
uv run landscape report examples/synthetic --format json --output generated/report/custom_report.json
uv run landscape report examples/synthetic --format schema
uv run landscape inspect examples/synthetic TREE001
uv run landscape inspect examples/synthetic HOUSE001
uv run landscape quantities examples/synthetic
uv run landscape quantities examples/synthetic --format csv
uv run landscape quantities examples/synthetic --format json
uv run landscape quantities examples/synthetic --format schema
uv run landscape references examples/synthetic --format json
uv run landscape references examples/synthetic --format schema
uv run landscape render examples/synthetic --sheet existing
```

The renderer writes:

```text
examples/synthetic/generated/svg/L1.0_existing_conditions.svg
```

## Project Files

A project can keep all schema data in `project.yaml`, or split bulky sections
into adjacent files. Currently supported split files:

```text
existing_conditions.yaml
references.yaml
```

`references.yaml` may contain:

```yaml
reference_documents: []
site_photos: []
```

The starter Greenleaf project uses this split-file layout:

```text
projects/greenleaf/project.yaml
projects/greenleaf/references.yaml
projects/greenleaf/existing_conditions.yaml
```

## Alternatives and phased work

Keep baseline measurements in the existing project and author design changes in
an optional `planning.yaml` sidecar. Generate portable review files:

```bash
uv run landscape compare examples/synthetic
uv run landscape phases examples/synthetic
```

The synthetic demonstration compares a larger patio against a garden alternative;
its two cumulative phases reach the selected patio design. Costs remain explicitly
unknown until sourced unit-rate ranges are supplied. These are software fixtures,
not designs or quotes for Greenleaf.

The review supports single or side-by-side snapshots, synchronized navigation,
entity inspection, Python-calculated quantity differences, dependencies and cost
allowances. `--planning`, `--output` and `--profile share|private` are supported.
See [Planning workflow](docs/PLANNING_WORKFLOW.md) for authoring semantics and
[Site capture guide](docs/SITE_CAPTURE_GUIDE.md) for the real-property inputs.

## Survey-based test plans and scoped exclusions

```bash
uv run landscape survey examples/constraints/traverse.yaml
uv run landscape render examples/constraints --format html
uv run landscape compare examples/constraints
```

The survey command reconstructs supplied bearings/distances and reports closure;
it does not extract dimensions from an image or certify survey accuracy. See
[Survey import](docs/SURVEY_IMPORT.md).

`existing_conditions.site_constraints` stores supplied pool exclusions as an
explicit polygon or `edge_index` plus `distance_ft`. Edge indices follow the
parcel's zero-based exterior sequence, including its closing edge. Distances use
that property edge, not a fence. `applies_to: [pool]` matches proposed hardscape
subtypes (case-insensitive); it does not prohibit planting. New overlaps fail
validation; existing conflicts and unverified source interpretation remain warnings.
The buffer is distance to the selected finite boundary segment with rounded ends,
clipped to the parcel; confirm the intended geometry when encoding a real restriction.

Existing fences can use `placement: context` to record observed alignment outside
the parcel with a warning. Proposed fences and other outside geometry still fail.
Purple fences, black boundaries, and translucent red exclusions have separate
layers and inspection metadata. Constraint shapes remain fixed across concepts.
Distant context can extend beyond the fixed drawing sheet.

`examples/constraints` is synthetic. A real-property first test should contain
transcribed boundary courses plus clearly marked approximate house/fence traces,
then be reconciled against clean survey details and current measurements before
using clearances or quantities to make construction decisions.
