# ADR 0001: Direct SVG Renderer for Initial Existing Conditions

## Decision

Generate the first existing-conditions drawing with deterministic direct SVG
string generation instead of adding a rendering library.

## Context

Milestone 0 and the minimum Milestone 1 slice require one vector output:
`L1.0 Existing Conditions`. The drawing needs parcel, structures, hardscape,
linear features, trees, planting beds, lawn, labels, north arrow, scale, and a
title block.

## Alternatives Considered

- `svgwrite`: convenient object API but another abstraction to learn and test.
- Direct SVG: simple, inspectable, stable, and sufficient for the first sheet.
- PDF-first rendering: premature because SVG is the primary initial target.

## Reason

Direct SVG keeps the first renderer small and deterministic. It also makes
structural tests straightforward because the output is plain text.

## Consequences

The renderer should stay narrow. If sheet composition, symbol reuse, or PDF
conversion grows materially more complex, introduce a renderer abstraction and
document that change in a later ADR.

