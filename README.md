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
