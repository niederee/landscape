# Project Progress

## Current Phase

Milestone 1 existing-conditions modeling.

## Decisions

- Use Python 3.13+ with a uv-native `pyproject.toml`.
- Keep project data in YAML and generated SVG as a reproducible output.
- Use Pydantic for schema validation and Shapely for deterministic geometry.
- Generate SVG directly for the first renderer to avoid an unnecessary rendering dependency.
- Keep the first drawing target to `L1.0 Existing Conditions`.
- Model utility features with either a point `location` or explicit `geometry`.
- Support utility clearance as either explicit `clearance_zone` geometry or a deterministic buffer from `clearance_radius_ft`.
- Calculate existing-condition quantities from structured geometry rather than drawings.

## Checklist

- [x] Evaluated `LANDSCAPE_PLANNER_SPEC.md`.
- [x] Created persistent progress tracking file.
- [x] Create Python package scaffold.
- [x] Implement core existing-conditions models.
- [x] Implement YAML project loading.
- [x] Implement validation rules.
- [x] Implement basic SVG renderer.
- [x] Implement `landscape validate`.
- [x] Implement `landscape render`.
- [x] Add synthetic fixture project.
- [x] Add initial Greenleaf project folder.
- [x] Add unit and integration tests.
- [x] Verify with tests and CLI commands.
- [x] Add utility/equipment model.
- [x] Add utility parcel containment validation.
- [x] Add utility clearance-zone validation and conflict warnings.
- [x] Render utility symbols and clearance zones on the existing-conditions SVG.
- [x] Add deterministic existing-conditions quantity reporting.
- [x] Add `landscape quantities`.

## Verification

- `python3 --version`: Python 3.13.3.
- `uv --version`: not globally installed on this machine.
- `.venv/bin/pip install uv`: installed uv locally in the project virtual environment.
- `.venv/bin/uv sync --extra dev`: passed.
- `.venv/bin/uv run pytest`: 6 passed.
- `.venv/bin/uv run landscape validate examples/synthetic`: passed with 0 errors and 0 warnings.
- `.venv/bin/uv run landscape render examples/synthetic --sheet existing`: generated `examples/synthetic/generated/svg/L1.0_existing_conditions.svg`.
- `.venv/bin/uv run landscape validate projects/greenleaf`: passed with starter placeholder geometry.
- `.venv/bin/uv run landscape render projects/greenleaf --sheet existing`: generated `projects/greenleaf/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-utilities-clearance`: `.venv/bin/uv run pytest`: 9 passed.
- Branch `milestone-1-utilities-clearance`: `.venv/bin/uv run landscape validate examples/synthetic`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-utilities-clearance`: `.venv/bin/uv run landscape render examples/synthetic --sheet existing`: generated `examples/synthetic/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-utilities-clearance`: `.venv/bin/uv run landscape validate projects/greenleaf`: passed with starter placeholder geometry.
- Branch `milestone-1-utilities-clearance`: `.venv/bin/uv run landscape render projects/greenleaf --sheet existing`: generated `projects/greenleaf/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-quantity-reporting`: `.venv/bin/uv run pytest`: 13 passed.
- Branch `milestone-1-quantity-reporting`: `.venv/bin/uv run landscape quantities examples/synthetic`: passed.
- Branch `milestone-1-quantity-reporting`: `.venv/bin/uv run landscape validate examples/synthetic`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-quantity-reporting`: `.venv/bin/uv run landscape render examples/synthetic --sheet existing`: generated `examples/synthetic/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-quantity-reporting`: `.venv/bin/uv run landscape quantities projects/greenleaf`: passed with starter placeholder quantities.
- Branch `milestone-1-quantity-reporting`: `.venv/bin/uv run landscape validate projects/greenleaf`: passed with starter placeholder geometry.
- Branch `milestone-1-quantity-reporting`: `.venv/bin/uv run landscape render projects/greenleaf --sheet existing`: generated `projects/greenleaf/generated/svg/L1.0_existing_conditions.svg`.

## Pull Request Status

- Working branch: `milestone-0-foundation`.
- Pushed branch: `origin/milestone-0-foundation`.
- Pull request: `https://github.com/niederee/landscape/pull/1`.
- Working branch: `milestone-1-utilities-clearance`.
- Pull request: `https://github.com/niederee/landscape/pull/2`.
- Working branch: `milestone-1-quantity-reporting`.

## Remaining Limitations

- Only schema version 1 is supported.
- Only `L1.0 Existing Conditions` SVG rendering is implemented.
- Greenleaf contains placeholder geometry that must be replaced by surveyed/measured data.
- Quantity reporting covers existing conditions only and does not yet calculate costs.
- Phase dependency validation, concepts, costs, PDF, and DXF remain future milestones.

## Next Smallest Useful Step

Add a machine-readable quantity export, likely CSV, after keeping the CLI table output
as the human-readable report.

## Resume Notes

Start by reading this file and `LANDSCAPE_PLANNER_SPEC.md`. Continue with the
next unchecked checklist item, then update this file before ending the session.
