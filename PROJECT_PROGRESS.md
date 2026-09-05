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
- Export existing-condition quantities as deterministic CSV for downstream analysis.
- Track source reference documents and site-photo survey metadata in structured project data.
- Validate entity `source.reference` values against declared reference document and photo IDs or filenames.
- Load optional `references.yaml` files for reference documents and site photos while preserving single-file project support.
- Split the Greenleaf starter project into separate metadata, reference, and existing-conditions YAML files.
- Inspect one project entity by stable ID from the CLI.
- Include calculated geometry metrics in `landscape inspect` output under a separate `calculated` block.
- List project entities deterministically so stable IDs are discoverable from the CLI.

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
- [x] Add machine-readable existing-conditions quantity CSV export.
- [x] Add structured reference document metadata.
- [x] Add structured site-photo metadata.
- [x] Add `landscape references`.
- [x] Validate source references against declared project metadata.
- [x] Add optional split-file loading for `references.yaml`.
- [x] Split Greenleaf into `project.yaml`, `references.yaml`, and `existing_conditions.yaml`.
- [x] Add `landscape inspect`.
- [x] Add calculated geometry metrics to `landscape inspect`.
- [x] Add `landscape list-entities`.

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
- Branch `milestone-1-quantity-csv`: `.venv/bin/uv run pytest`: 16 passed.
- Branch `milestone-1-quantity-csv`: `.venv/bin/uv run landscape quantities examples/synthetic --format csv`: generated `examples/synthetic/generated/csv/existing_conditions_quantities.csv`.
- Branch `milestone-1-quantity-csv`: `.venv/bin/uv run landscape quantities projects/greenleaf --format csv`: generated `projects/greenleaf/generated/csv/existing_conditions_quantities.csv`.
- Branch `milestone-1-quantity-csv`: `.venv/bin/uv run landscape validate examples/synthetic`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-quantity-csv`: `.venv/bin/uv run landscape render examples/synthetic --sheet existing`: generated `examples/synthetic/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-quantity-csv`: `.venv/bin/uv run landscape validate projects/greenleaf`: passed with starter placeholder geometry.
- Branch `milestone-1-reference-metadata`: `.venv/bin/uv run pytest`: 20 passed.
- Branch `milestone-1-reference-metadata`: `.venv/bin/uv run landscape references examples/synthetic`: passed.
- Branch `milestone-1-reference-metadata`: `.venv/bin/uv run landscape validate examples/synthetic`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-reference-metadata`: `.venv/bin/uv run landscape render examples/synthetic --sheet existing`: generated `examples/synthetic/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-reference-metadata`: `.venv/bin/uv run landscape references projects/greenleaf`: passed.
- Branch `milestone-1-reference-metadata`: `.venv/bin/uv run landscape validate projects/greenleaf`: passed with starter placeholder geometry.
- Branch `milestone-1-reference-metadata`: `.venv/bin/uv run landscape quantities examples/synthetic --format csv`: generated `examples/synthetic/generated/csv/existing_conditions_quantities.csv`.
- Branch `milestone-1-reference-metadata`: `.venv/bin/uv run landscape quantities projects/greenleaf --format csv`: generated `projects/greenleaf/generated/csv/existing_conditions_quantities.csv`.
- Branch `milestone-1-reference-metadata`: `.venv/bin/uv run landscape --help`: listed `references`.
- Branch `milestone-1-split-references`: `.venv/bin/uv run pytest`: 22 passed.
- Branch `milestone-1-split-references`: `.venv/bin/uv run landscape validate tests/fixtures/split_references`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-split-references`: `.venv/bin/uv run landscape references tests/fixtures/split_references`: passed.
- Branch `milestone-1-split-greenleaf`: `.venv/bin/uv run pytest`: 23 passed.
- Branch `milestone-1-split-greenleaf`: `.venv/bin/uv run landscape validate projects/greenleaf`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-split-greenleaf`: `.venv/bin/uv run landscape references projects/greenleaf`: passed.
- Branch `milestone-1-split-greenleaf`: `.venv/bin/uv run landscape quantities projects/greenleaf --format csv`: generated `projects/greenleaf/generated/csv/existing_conditions_quantities.csv`.
- Branch `milestone-1-split-greenleaf`: `.venv/bin/uv run landscape render projects/greenleaf --sheet existing`: generated `projects/greenleaf/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-inspect-entity`: `.venv/bin/uv run pytest`: 29 passed.
- Branch `milestone-1-inspect-entity`: `.venv/bin/uv run landscape --help`: listed `inspect`.
- Branch `milestone-1-inspect-entity`: `.venv/bin/uv run landscape validate examples/synthetic`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-inspect-entity`: `.venv/bin/uv run landscape validate projects/greenleaf`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-inspect-entity`: `.venv/bin/uv run landscape render projects/greenleaf --sheet existing`: generated `projects/greenleaf/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-inspect-entity`: `.venv/bin/uv run landscape inspect projects/greenleaf PARCEL001`: passed.
- Branch `milestone-1-inspect-entity`: `.venv/bin/uv run landscape inspect examples/synthetic TREE001`: passed.
- Branch `milestone-1-inspect-metrics`: `.venv/bin/uv run pytest`: 33 passed.
- Branch `milestone-1-inspect-metrics`: `.venv/bin/uv run landscape inspect examples/synthetic HOUSE001`: reported area, perimeter, centroid, and bounds.
- Branch `milestone-1-inspect-metrics`: `.venv/bin/uv run landscape inspect examples/synthetic UTIL001`: reported clearance area and bounds.
- Branch `milestone-1-inspect-metrics`: `.venv/bin/uv run landscape validate projects/greenleaf`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-inspect-metrics`: `.venv/bin/uv run landscape render projects/greenleaf --sheet existing`: generated `projects/greenleaf/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-list-entities`: `.venv/bin/uv run pytest`: 37 passed.
- Branch `milestone-1-list-entities`: `.venv/bin/uv run landscape --help`: listed `list-entities`.
- Branch `milestone-1-list-entities`: `.venv/bin/uv run landscape list-entities examples/synthetic`: listed 17 inspectable entities.
- Branch `milestone-1-list-entities`: `.venv/bin/uv run landscape list-entities examples/synthetic --category tree`: listed 3 tree entities.
- Branch `milestone-1-list-entities`: `.venv/bin/uv run landscape list-entities projects/greenleaf`: listed 3 starter entities.
- Branch `milestone-1-list-entities`: `.venv/bin/uv run landscape validate examples/synthetic`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-list-entities`: `.venv/bin/uv run landscape validate projects/greenleaf`: passed with 0 errors and 0 warnings.
- Branch `milestone-1-list-entities`: `.venv/bin/uv run landscape render projects/greenleaf --sheet existing`: generated `projects/greenleaf/generated/svg/L1.0_existing_conditions.svg`.
- Branch `milestone-1-list-entities`: `.venv/bin/uv run landscape inspect projects/greenleaf PARCEL001`: passed.

## Pull Request Status

- Working branch: `milestone-0-foundation`.
- Pushed branch: `origin/milestone-0-foundation`.
- Pull request: `https://github.com/niederee/landscape/pull/1`.
- Working branch: `milestone-1-utilities-clearance`.
- Pull request: `https://github.com/niederee/landscape/pull/2`.
- Working branch: `milestone-1-quantity-reporting`.
- Pull request: `https://github.com/niederee/landscape/pull/3`.
- Working branch: `milestone-1-quantity-csv`.
- Pull request: `https://github.com/niederee/landscape/pull/4`.
- Working branch: `milestone-1-reference-metadata`.
- Pull request: `https://github.com/niederee/landscape/pull/5`.
- Working branch: `milestone-1-split-references`.
- Pull request: `https://github.com/niederee/landscape/pull/6`.
- Working branch: `milestone-1-split-greenleaf`.
- Pull request: `https://github.com/niederee/landscape/pull/7`.
- Working branch: `milestone-1-inspect-entity`.
- Pull request: `https://github.com/niederee/landscape/pull/8`.
- Working branch: `milestone-1-inspect-metrics`.
- Pull request: `https://github.com/niederee/landscape/pull/9`.
- Working branch: `milestone-1-list-entities`.

## Remaining Limitations

- Only schema version 1 is supported.
- Only `L1.0 Existing Conditions` SVG rendering is implemented.
- Greenleaf contains split-file placeholder geometry that must be replaced by surveyed/measured data.
- Reference records do not require local files to exist yet and do not parse document contents.
- Split-file loading currently supports `existing_conditions.yaml` and `references.yaml`.
- Inspection metrics are read-only derived values and are not written back to source YAML.
- Entity listing uses current schema categories and does not yet include concept/master-plan entities.
- Quantity reporting and CSV export cover existing conditions only and do not yet calculate costs.
- Phase dependency validation, concepts, costs, PDF, and DXF remain future milestones.

## Next Smallest Useful Step

Add a basic existing-conditions report command that combines validation status,
entity counts, quantities, and reference summaries for project review.

## Resume Notes

Start by reading this file and `LANDSCAPE_PLANNER_SPEC.md`. Continue with the
next unchecked checklist item, then update this file before ending the session.
