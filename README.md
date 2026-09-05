# Landscape Planner

Deterministic residential landscape planning from structured YAML data.

The project follows the workflow in `LANDSCAPE_PLANNER_SPEC.md`: structured
property data is the source of truth, geometry calculations are deterministic,
and generated drawings are reproducible outputs.

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
uv run landscape quantities examples/synthetic
uv run landscape quantities examples/synthetic --format csv
uv run landscape render examples/synthetic --sheet existing
```

The renderer writes:

```text
examples/synthetic/generated/svg/L1.0_existing_conditions.svg
```
