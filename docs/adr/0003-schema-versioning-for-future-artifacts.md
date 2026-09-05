# ADR 0003: Schema Versioning for Future Generated Artifacts

## Status

Accepted

## Decision

Generated artifacts that become part of automation or downstream integrations must follow the same
explicit schema-versioning approach used for report payloads.

This applies immediately to:

- Quantities machine-readable artifacts (for example, JSON or CSV+schema pairs).
- Reference manifests (documents and photos in a machine-readable format).

For each artifact family:

- Keep a single source-of-truth version constant in code.
- Publish a schema file alongside machine-readable output when supported.
- Reject silent interpretation changes by treating breaking changes as version bumps.

## Policy

- On each breaking schema change for a given artifact family, bump its artifact version and update
  migration notes in:
  - this ADR,
  - `PROJECT_PROGRESS.md`,
  - and relevant command documentation.
- Add parser-level migration gates that reject unsupported artifact schema versions with a
  clear migration message.
- Keep schema-bearing artifacts stable and deterministic:
  - consistent key ordering,
  - deterministic entity ordering,
  - stable float formatting.
- Keep a discoverable supported-version list and migration note map in the artifact module.

## Migration Notes

- `1.0.0` (Implemented): versioned machine-readable outputs:
  - `generated/quantities/existing_conditions_quantities.json`
  - `generated/quantities/existing_conditions_quantities.schema.json`
  - `generated/references/landscape_references.json`
  - `generated/references/landscape_references.schema.json`
- `1.0.0` (Stable): strict parser checks are active for report, quantities,
  and reference manifest artifacts.
