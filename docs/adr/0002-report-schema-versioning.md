# ADR 0002: Report Schema Versioning and Migration Policy

## Status

Accepted

## Decision

Report payloads emitted by `landscape report --format json` must include
`schema_version`, and schema changes will be treated with explicit versioning
and compatibility notes.

## Context

Milestone 1 now produces machine-readable report artifacts:

- `generated/report/landscape_report.json`
- `generated/report/landscape_report.schema.json`
- `generated/report/landscape_report.csv`

As these files are consumed by CI and downstream tools, unannounced schema
changes would reduce reproducibility and require risky, silent remediations.

## Policy

- Keep `REPORT_SCHEMA_VERSION` in
  `src/landscape_planner/analysis/reporting.py` as the single source of truth.
- Require schema-version checks in tests for stable payload shape and required fields.
- Keep parser-level compatibility checks for report payload consumers.
- On any breaking report-payload change,:
  - increment `REPORT_SCHEMA_VERSION`,
  - update migration notes in this ADR and this section of the project
    documentation,
  - add/update tests that validate compatibility behavior.

## Migration Notes

- `1.0.0`: Initial report schema with stable keys:
  `schema_version`, `project_id`, `validation`, `entity_counts`,
  `quantity_totals`, and `references`.
