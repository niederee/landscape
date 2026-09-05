# ADR 0004: Standalone existing-conditions review export

## Status

Accepted direction for the H1 implementation. Acceptance evidence is recorded in
`PROJECT_PROGRESS.md`; this ADR does not certify completion of all release gates.

## Context

At baseline `7bd72cd63ac23575ab5d92985fce35ad369a89e8`, the project has
reusable deterministic SVG, entity inspection, quantities, and validation, but no
HTML output or concept/phase resolver. The homeowner needs a file that can be
shared and inspected without installing Python. The standalone HTML addendum was
written before repository access was available; `docs/PROJECT_DIRECTION_REVIEW.md`
now reconciles that proposal with actual code.

## Decision

Add HTML as an optional format of the existing `landscape render` command. Keep
SVG the default and retain `--sheet existing` as the only H1 snapshot. H1 is a
read-only document with a small browser runtime, not an authoring application.

Integration boundaries:

| Existing module | H1 responsibility |
|---|---|
| `io/yaml_loader.py` | Continue loading canonical schema-1 data unchanged. |
| `analysis/validation.py` | Validate before packaging; reuse warning/error semantics. Fix demonstrated unsupported-input/identity defects rather than bypass them. |
| `rendering/svg.py` | Supply the same deterministic geometry to both outputs; add semantic entity associations and correct orientation/painting defects where necessary. |
| `inspection.py` and `estimating/quantities.py` | Supply entity metrics and whole-plan quantities. Browser layer visibility does not recalculate quantities. |
| New `rendering/html.py` and maintained viewer assets | Apply export privacy policy, embed SVG/data/CSS/JavaScript, and supply navigation, layers, search and inspection. |
| `cli/main.py` | Select format/profile, provide actionable validation failure, choose output path and write a complete artifact. |

The complete file must work when copied alone and opened via `file://` without
networking. Embed all required resources; do not fetch sidecar JSON, fonts, CDN
scripts, or maps. Include a readable default plan and summary without JavaScript.
Use standard controls with keyboard access and a searchable entity list.

Default sharing must filter unnecessary identifying/source content before both
SVG and JSON serialization. Do not embed source files or a photo archive. A private
profile can retain additional metadata; neither profile silently publishes it.
Use context-appropriate escaping, text-only DOM insertion, and a restrictive CSP.
Keep project values out of executable JavaScript and hash the trusted inline
assets. Private-string canaries must be absent throughout share output.

Use stable ordering, IDs and a versioned viewer payload. Distinguish source-data
digest from exporter identity; exclude wall-clock timestamps from deterministic
bytes. A new HTML output does not require a project-schema migration. The viewer
payload is internal to this self-contained output; defer public import/migration
APIs until a consumer exists.

The SVG renderer maps local feet into sheet coordinates with positive Y upward
in the model and downward in SVG. H1 navigation changes presentation only. Preserve
the renderer's scale and orientation; do not reinterpret SVG pixels as feet.
The ruler and synchronized comparison wait for H2's tested coordinate contract.
Print styles restore a complete review view and label screen/browser print scale
appropriately; arbitrary browser printing is not a calibrated construction sheet.

## Alternatives considered

- **Full web editor:** much larger authoring, persistence and geometry scope;
  unnecessary to review the current plan.
- **Independent JavaScript renderer/calculator:** creates two implementations that
  can disagree about geometry and quantities.
- **Hosted viewer or ZIP bundle:** useful in other settings, but does not meet the
  requested one-file portability and offline contract.
- **SVG only until every planning subsystem exists:** preserves simplicity but
  delays practical review of the site data needed to develop those subsystems.

## Consequences and release gates

The browser can only show modeled information. Costs, scenarios, phases and
advanced analysis remain unavailable until the Python core supports them.
Greenleaf remains provisional until actual property data replaces its starter
geometry. Use synthetic projects for public demonstrations.

Before calling H1 complete, run the addendum's relevant HTML-001 through HTML-015
gates: copied-file offline interactions and request monitoring, JavaScript-disabled
fallback, consistent selection/layers/metrics, geometry parity, hostile content,
privacy, deterministic bytes, invalid-input handling, regression tests, CSP and
explicit treatment of unknowns. Inspect a representative export visually. Record
the browser/version and any unrun gate; Chromium evidence alone does not establish
Safari, Firefox or mobile support.

This decision narrows the original specification's sections 60 and 89: defer
graphical authoring, while allowing generated interactive review now. It preserves
the deterministic source-of-truth, existing-conditions accuracy and professional
scope principles. H2/H3 need separate tested core work, not placeholder controls.
