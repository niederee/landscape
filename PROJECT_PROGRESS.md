# Project Progress

## Current Phase

Milestone 0 plus the minimum Milestone 1 foundation from
`LANDSCAPE_PLANNER_SPEC.md` section 100.

## Decisions

- Use Python 3.13+ with a uv-native `pyproject.toml`.
- Keep project data in YAML and generated SVG as a reproducible output.
- Use Pydantic for schema validation and Shapely for deterministic geometry.
- Generate SVG directly for the first renderer to avoid an unnecessary rendering dependency.
- Keep the first drawing target to `L1.0 Existing Conditions`.

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

## Pull Request Status

- Working branch: `milestone-0-foundation`.
- Pushed branch: `origin/milestone-0-foundation`.
- PR URL: `https://github.com/niederee/landscape/pull/new/milestone-0-foundation`.
- `gh` is not installed and no `GITHUB_TOKEN` or `GH_TOKEN` is available, so PR creation could not be completed programmatically from this shell.

## Remaining Limitations

- Only schema version 1 is supported.
- Only `L1.0 Existing Conditions` SVG rendering is implemented.
- Greenleaf contains placeholder geometry that must be replaced by surveyed/measured data.
- Utility models, phase dependency validation, concepts, costs, PDF, and DXF remain future milestones.

## Next Smallest Useful Step

Add utility/equipment modeling and validation for required clearance zones, then expand
the Greenleaf source files as real property measurements become available.

## Resume Notes

Start by reading this file and `LANDSCAPE_PLANNER_SPEC.md`. Continue with the
next unchecked checklist item, then update this file before ending the session.
