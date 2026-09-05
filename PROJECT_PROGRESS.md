# Project Progress

## Current Phase

H1 portable existing-conditions review, alongside real-site capture.

## Current Review and Implementation (September 5, 2026)

- Audited freshly cloned `main` at `7bd72cd63ac23575ab5d92985fce35ad369a89e8`;
  baseline regression suite: **62 passed** on Python 3.13.3.
- Direction and actual gaps: `docs/PROJECT_DIRECTION_REVIEW.md`.
- Architecture decision: `docs/adr/0004-standalone-review-export.md`.
- Implementation branch: `feat/portable-landscape-review`.
- Initial implementation commit: `6bcbb4c` (local). Publishing is blocked:
  connector commit-tree creation returned HTTP 403, and local Git has no push
  credentials. No remote branch, PR or CI result is claimed. Reconnect a GitHub
  installation authorized to write `niederee/landscape`, then publish this branch.
- Added `render --format html --profile share|private`, preserving SVG default.
  `rendering/html.py` embeds the canonical SVG, navigation, layers, search,
  linked feature inspection, quantities, static provenance and validation.
- Share metadata filtering occurs before serialization; hostile text is escaped,
  trusted inline assets use CSP hashes, exports are deterministic and atomic,
  and the CLI protects source files and reference assets from overwrite.
- Fixed parcel selection, north-arrow painting/orientation, nested door ID/source
  checks and non-LineString validation. North rotation is clockwise from local
  +Y; it changes the arrow, not authoritative site geometry.
- Successfully generated synthetic and Greenleaf HTML and the synthetic SVG.
  Example paths: `examples/synthetic/generated/html/L1.0_existing_conditions.html`
  and `projects/greenleaf/generated/html/L1.0_existing_conditions.html`.
  Synthetic source files are missing (2 warnings); Greenleaf survey is pending
  (1 warning). These remain warnings under existing validation policy.
- Updated suite: `uv run pytest -q` returned **85 passed, 2 skipped**.
  The two skips are actual-browser tests; explicitly requiring the browser with
  `LANDSCAPE_REQUIRE_BROWSER=1` correctly fails while Chromium is absent.
- Browser installation was attempted but Chromium downloads timed out locally.
  Actual offline browser interaction, CSP enforcement and visual layout remain
  **not verified locally**. Browser tests exist; CI installs Chromium and requires
  the browser tests instead of accepting an executable-missing skip.
- Greenleaf has **not** been validated against the physical property. Its parcel
  and house are low-confidence starter estimates.

### Active acceptance status

| Gate | Evidence / status |
|---|---|
| One-file generation, SVG geometry parity, deterministic bytes | Automated renderer/CLI tests and generated fixtures |
| Privacy canaries, hostile text, source overwrite protection, invalid geometry | Automated unit/integration tests |
| Copied-file offline navigation, layers, inspection, static fallback, CSP | Browser tests added; local run skipped because browser unavailable |
| Visual layout, Firefox/Safari/Edge and mobile compatibility | Not certified |
| Real property, design alternatives and cumulative phasing | Not implemented/verified |

Historical decisions and command records below are retained for provenance;
they are not a list of commands rerun in this review.

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
- Add a basic existing-conditions report command for consolidated review output.
- Add report export formats for downstream workflows.
- Add machine-readable report schema and deterministic default artifact locations.
- Add explicit schema-version compatibility checks for report payloads.
- Add migration notes for breaking report schema changes.
- Add migration notes for other schema-bearing artifacts (quantities and reference manifests).

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
- [x] Add `landscape report`.
- [x] Add machine-readable report schema and default report artifact locations.
- [x] Add schema-version compatibility checks for report payloads.
- [x] Add migration notes for breaking report schema changes.
- [x] Add migration notes for other schema-bearing artifacts (quantities and reference manifests).
- [x] Add schema-versioned JSON and schema export for quantities.
- [x] Add schema-versioned JSON and schema export for references.
- [x] Add schema-version migration checks and parser gates for report, quantity, and reference artifacts.
- [x] Add CLI-aware validation for missing local reference asset files with warning codes.
- [x] Add `landscape validate --strict` to fail fast on warning messages.

## Verification

- `python3 --version`: Python 3.13.3.
- `uv --version`: not globally installed on this machine.
- `.venv/bin/pip install uv`: installed uv locally in the project virtual environment.
- `.venv/bin/uv sync --extra dev`: passed.
- `.venv/bin/uv run pytest`: 60 passed.
- `.venv/bin/uv run pytest`: 62 passed.
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
- Branch `milestone-1-existing-conditions-report`: `.venv/bin/uv run landscape --help` will include `report`.
- Branch `milestone-1-existing-conditions-report`: `.venv/bin/uv run landscape report projects/greenleaf` is ready to verify once merged.
- Branch `milestone-1-report-export`: `.venv/bin/uv run landscape report projects/greenleaf --format json` writes
  `projects/greenleaf/generated/report/landscape_report.json`.
- Branch `milestone-1-report-export`: `.venv/bin/uv run landscape report projects/greenleaf --format schema` writes
  `projects/greenleaf/generated/report/landscape_report.schema.json`.
- Branch `milestone-1-report-schema-stability`: `.venv/bin/uv run pytest tests/unit/test_report_schema.py`.
- Branch `milestone-1-report-schema-migrations`: Migration policy docs for report schema changes.
- Branch `milestone-1-validate-strict-mode`: `.venv/bin/uv run pytest`: 62 passed.
- Branch `milestone-1-validate-strict-mode`: `.venv/bin/uv run landscape validate tests/fixtures/synthetic`: passes with warnings and exit code 0.
- Branch `milestone-1-validate-strict-mode`: `.venv/bin/uv run landscape validate tests/fixtures/synthetic --strict`: exits with code 1.
- Working branch: `milestone-1-schema-planning`.
- Pull request: `https://github.com/niederee/landscape/pull/16`.
- Working branch: `milestone-1-quantities-reference-schema`.
- Pull request: `https://github.com/niederee/landscape/pull/17`.
- Working branch: `milestone-1-schema-migration-checks`.
- Pull request: `https://github.com/niederee/landscape/pull/18`.
- Working branch: `milestone-1-reference-asset-warnings`.
- Pull request: `https://github.com/niederee/landscape/pull/19`.
- Working branch: `milestone-1-validate-strict-mode`.
- Pull request: `https://github.com/niederee/landscape/pull/20`.


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
- Pull request: `https://github.com/niederee/landscape/pull/10`.
- Merged pull request: `https://github.com/niederee/landscape/pull/11`.
- Working branch: `milestone-1-report-export`.
- Pull request: `https://github.com/niederee/landscape/pull/12`.
- Working branch: `milestone-1-report-schema`.
- Pull request: `https://github.com/niederee/landscape/pull/13`.
- Working branch: `milestone-1-report-schema-stability`.
- Pull request: `https://github.com/niederee/landscape/pull/14`.
- Working branch: `milestone-1-report-schema-migrations`.
- Pull request: `https://github.com/niederee/landscape/pull/15`.
- Working branch: `milestone-1-schema-planning`.
- Pull request: `https://github.com/niederee/landscape/pull/16`.
- Working branch: `milestone-1-quantities-reference-schema`.
- Pull request: `https://github.com/niederee/landscape/pull/17`.
- Working branch: `milestone-1-reference-asset-warnings`.
- Pull request: `https://github.com/niederee/landscape/pull/19`.

## Remaining Limitations

- Only schema version 1 is supported.
- Only `L1.0 Existing Conditions` SVG and standalone HTML rendering are implemented.
- HTML omits doors, easements, setbacks and rights-of-way from the drawing and
  explicitly identifies these omissions. Label collision layout and dimensioned
  construction sheets remain future work.
- Greenleaf contains split-file placeholder geometry that must be replaced by surveyed/measured data.
- Missing local reference assets now emit warnings; strict mode fails the command when warnings are present.
- Split-file loading currently supports `existing_conditions.yaml` and `references.yaml`.
- Inspection metrics are read-only derived values and are not written back to source YAML.
- Entity listing uses current schema categories and does not yet include concept/master-plan entities.
- Quantity reporting and CSV export cover existing conditions only and do not yet calculate costs.
- Phase dependency validation, concepts, costs, PDF, and DXF remain future milestones.

## Next Smallest Useful Step

- Complete the browser/visual H1 gates, then replace Greenleaf placeholders using
  the owner's survey and field observations. See the ordered capture checklist
  in `docs/PROJECT_DIRECTION_REVIEW.md`.
- After site capture, implement a small immutable-baseline concept resolver and
  two authored alternatives that answer one actual homeowner design question.

## Resume Notes

Read the current section, `docs/PROJECT_DIRECTION_REVIEW.md`, and the two specs.
Use the active acceptance gaps and next useful outcome, not old branch logs, to
choose work. Record executed evidence and unverified limitations separately.
