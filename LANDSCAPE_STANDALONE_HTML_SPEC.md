# Landscape Planner: Standalone HTML Review Package and Next-Step Specification

**Status:** Adopted direction; baseline reviewed and first HTML slice implemented in the accompanying PR
**Prepared:** September 5, 2026  
**Target repository:** `niederee/landscape`, branch `main`  
**Reviewed commit:** Not available; no repository commit was retrieved  
**Intended reader:** Coding agent with access to the repository and the homeowner/developer

**Repository reconciliation:** The original access limitation below is historical.
The current audit is in [`docs/PROJECT_DIRECTION_REVIEW.md`](docs/PROJECT_DIRECTION_REVIEW.md),
with implementation decisions in [`docs/adr/0004-standalone-review-export.md`](docs/adr/0004-standalone-review-export.md).
`PROJECT_PROGRESS.md` records executed verification and remaining release gaps.
H2–H4 remain proposals; this document is not a claim that every H1 gate or
target browser has been certified.

> Evidence limitation: The GitHub connector returned HTTP 404 for the repository, `main`, `LANDSCAPE_PLANNER_SPEC.md`, and `PROJECT_PROGRESS.md`. Public-page and raw-file retrieval did not produce repository content. Therefore, this document does **not** claim to have reviewed the current implementation, validated progress claims, or run its tests. Its recommendations are based on the original specification provided in this conversation, the homeowner's request for standalone HTML, and the browser documentation referenced below. The original conversation specification is not a substitute for the current repository specification.
>
> Before changing implementation, the coding agent must complete the repository reconciliation in Section 2. Do not interpret any proposed module, command, schema, or missing capability below as a finding about current `main`.

## 1. Recommended Direction

Make a **self-contained, read-only HTML review package** a first-class optional output. Preserve the deterministic project model and existing output formats. Do not pivot to a browser-first CAD editor or rewrite the geometry engine in JavaScript.

The intended experience is:

```text
Homeowner edits structured project data or accepts reviewed design changes
                              |
                     Existing Python pipeline
                   validate -> resolve -> calculate
                              |
              One consistent plan/presentation snapshot
                       /               \
          Existing SVG/PDF outputs    Standalone HTML
                                     plan + inspection
                                     comparisons + phases
                                     quantities + warnings
```

The HTML is a **portable design-review document**, not the source of truth and not a live service. It should make the same plans easier to understand and compare without requiring recipients to install the software.

### 1.1 Keep, change, and defer

| Decision | Recommendation |
|---|---|
| Authoritative project data | Keep the repository's structured project model and versioned sources. |
| Geometry, validation, quantities, and costs | Keep authoritative calculations in the existing deterministic core. |
| SVG/PDF/DXF investments | Preserve functioning exporters. Reuse the existing SVG geometry rather than replacing it. |
| HTML priority | Bring a small standalone viewer forward; do not wait for every planned technical sheet. |
| “No GUI initially” | Interpret as “no full authoring application initially,” not “no interactive output.” |
| Main user outcome | Prioritize reviewing the real site and comparing meaningful alternatives over adding more entity classes. |
| New web stack | Do not require a server, database, login, React rewrite, or online deployment for this output. |
| Automatic design and simulation | Defer until measured site data, useful manual concepts, and validation are reliable. |

The measurable product outcome is not “the project exports HTML.” It is:

> A homeowner can open one file, understand the source quality of the plan, inspect features, compare available alternatives, and discuss what to build next without installing the application.

## 2. Mandatory First Step: Reconcile This Proposal with Actual `main`

### 2.1 Establish the baseline without disturbing the workspace

Inspect working-tree status and respect uncommitted work. Obtain the current `main` commit where access permits; record the exact SHA and whether it is a freshly fetched remote revision or a potentially stale local reference. Do not reset, force-checkout, or overwrite the developer's branch.

Read at that revision:

- `LANDSCAPE_PLANNER_SPEC.md` and `PROJECT_PROGRESS.md` in full.
- Repository instructions, README, package configuration, dependency lockfile, and CI configuration.
- Actual model, loading, validation, concept resolution, rendering, exporting, and CLI entry points.
- Relevant tests, fixtures, reference-project data, and generated examples.

Run the repository's documented test and example-generation commands. Record exact commands, environment, outcomes, failures, and unavailable dependencies. A stated milestone or test count in a Markdown file is not evidence that the behavior currently works.

Inspect representative output visually as well as structurally. Passing geometry tests alone does not establish readable drawings.

### 2.2 Required audit artifact

Produce `docs/reviews/MAIN_BASELINE_REVIEW.md` or the nearest existing equivalent. Use actual repository conventions rather than creating a competing documentation system.

| Capability | Documentation claim | Implementation evidence | Test or artifact evidence | Verified status | Smallest needed change |
|---|---|---|---|---|---|
| Project loading and schema | To inspect | To inspect | To inspect | Unverified | Determine from code |
| Geometry/provenance/units | To inspect | To inspect | To inspect | Unverified | Determine from code |
| SVG rendering and layers | To inspect | To inspect | To inspect | Unverified | Determine from code |
| Existing HTML support | To inspect | To inspect | To inspect | Unverified | Extend if already present |
| Concepts and immutability | To inspect | To inspect | To inspect | Unverified | Determine from code |
| Quantities and estimates | To inspect | To inspect | To inspect | Unverified | Determine from code |
| Phase resolution | To inspect | To inspect | To inspect | Unverified | Determine from code |
| Real-site completeness | To inspect | To inspect | To inspect | Unverified | Identify missing measurements |
| Tests and CI | To inspect | To inspect | To inspect | Unverified | Determine from execution |

Use statuses such as **verified working**, **implemented but not verified**, **partial**, **planned**, and **blocked**. Link evidence to commit-pinned paths and line ranges where possible. Distinguish defects from recommendations and from unknowns.

### 2.3 Implementation branch decision

If HTML already exists, harden and extend it against this contract. If reusable SVG exists, build a thin packaging adapter around it. If neither exists, finish the minimum accurate SVG slice first. Do not invent a second renderer to bypass an incomplete first one.

No repository-wide refactor is authorized by this proposal. Resolve conflicts with existing architecture in a short ADR and preserve working behavior.

## 3. Specification Precedence and Scope

After reconciliation and adoption, this addendum should supersede only the earlier document's **output priorities, viewer scope, and related acceptance criteria**. It should not silently replace the project schema, naming conventions, CLI, or established features.

Use `H0`–`H4` for this workstream, so that existing milestone numbers remain meaningful. Keep the long-term landscape master-plan goals, but express the next implementation work through small, testable releases.

Normative terms in this document:

- **MUST:** Required for the relevant release to pass.
- **SHOULD:** Expected unless a documented repository-specific reason justifies another approach.
- **MAY:** Optional and not a prerequisite.

All filenames and commands proposed below are examples until the audit maps them to real repository conventions.

## 4. Definition of “Standalone HTML”

The generated artifact MUST:

1. Be a single `.html` file that can be opened directly through `file://` in supported desktop browsers.
2. Contain its required SVG, styles, JavaScript, plan data, legends, and included media.
3. Operate with networking disabled, without a Python process, local web server, account, API key, or application installation.
4. Continue to work after copying only that file into an unrelated directory.
5. Avoid runtime CDN dependencies, external stylesheets, external scripts, remote fonts, map tiles, API calls, analytics, and adjacent JSON/SVG/image files.
6. Present a readable default plan and basic information without JavaScript; interactive controls may then be unavailable.

“Offline after an initial online load” does not satisfy this definition. Neither does “run a localhost server first.” Browser restrictions around local-file requests are the reason to embed dependencies rather than fetch sibling files. [B1]

The initial browser support target is desktop Chrome, Edge, Firefox, and Safari. Record versions actually tested. Responsive tablet layout is desirable, but opening downloaded HTML through mobile file-manager or attachment-preview workflows is a separate compatibility question; do not advertise it without testing.

Build-time tooling is allowed. A bundled JavaScript runtime may be produced during development, but the recipient MUST NOT need Node or a package manager.

## 5. Minimal Architecture: Extend, Do Not Rebuild

### 5.1 Responsibility boundary

| Responsibility | Deterministic core | HTML viewer |
|---|---|---|
| Read canonical project files | Authoritative | No |
| Validate site geometry and references | Authoritative | Display results |
| Resolve concepts and phase states | Authoritative | Select supplied snapshots |
| Compute model areas, lengths, quantities, and costs | Authoritative | Display supplied results |
| Construct plan geometry | Existing renderer | Display it |
| Pan, zoom, layers, selection, search | Supply stable identifiers | Yes |
| Cursor-to-world coordinate conversion | Supply transform contract | Yes |
| Temporary distance measurement | Supply units/transform | Yes, marked exploratory |
| Edit canonical geometry | Existing reviewed workflow | Out of scope initially |
| Feedback comments | Validate on import later | Optional review-data export |

Do not reproduce Shapely operations, concept resolution, grading rules, or cost estimation in the browser. A temporary ruler is not a second authoritative quantity engine.

### 5.2 Small internal presentation contract

Introduce a presentation/export adapter only if no adequate abstraction already exists. Its job is to connect generated vector geometry with inspector metadata and report values.

A suitable conceptual interface is:

```python
# Illustrative interface: adapt names and types to the repository.
bundle = build_review_bundle(project, export_options)
html = render_standalone_html(bundle)
write_export_atomically(output_path, html)
```

The bundle SHOULD include:

```text
manifest and provenance
available scenarios and phase snapshots
shared coordinate frame
rendered SVG per included snapshot or reusable generated components
entity inspection index
layer definitions and default visibility
quantities, warnings, and available comparison metrics
approved media assets
```

Do not create a general-purpose scene graph, plugin framework, event bus, or serialization ecosystem solely for the first HTML output. If the renderer already provides semantic SVG groups, use them.

### 5.3 Separate three kinds of state

**Project state** is canonical source data and resolved design state. **Presentation state** is selected scenario, visible layers, zoom, and highlighted feature. **Review state** is optional comments or saved preferences.

Changing a checkbox in the viewer MUST NOT modify project facts, recalculate the design, or imply that the source YAML has been saved.

## 6. Snapshot and Data Contract

Use a separately versioned viewer payload, independent of the project schema. Export plain JSON-safe values, not Python object serialization or executable expressions.

An illustrative payload fragment is:

```json
{
  "viewer_schema_version": 1,
  "project": {
    "id": "greenleaf",
    "title": "Landscape Review",
    "source_digest": "<computed source digest>",
    "data_status": "conceptual"
  },
  "coordinate_frame": {
    "type": "local_cartesian",
    "horizontal_units": "ft",
    "bounds": [0.0, 0.0, 80.0, 130.0]
  },
  "snapshots": [
    {
      "id": "existing",
      "scenario_id": "existing",
      "phase_id": null,
      "entity_ids": ["STRUCT001", "TREE001"],
      "metrics": {},
      "validation_summary": {
        "errors": 0,
        "warnings": 1
      }
    }
  ]
}
```

The numbers above are **synthetic examples**, not measurements of the homeowner's property. This fragment is not a replacement project schema.

Requirements:

- Stable project, scenario, snapshot, entity, and layer identifiers.
- Explicit units, coordinate interpretation, and source revision.
- Explicit capability flags so the viewer does not invent unsupported sections.
- Missing values represented as missing/unknown, not zero or fabricated estimates.
- Per-snapshot entity metadata where an entity changes across alternatives.
- Display precision independent of calculation precision and limited by source accuracy.
- No absolute developer-machine paths in shared output.

Local Cartesian feet MUST NOT be presented as geographic longitude/latitude. Do not call the payload standard geographic GeoJSON unless it actually satisfies that interchange format.

## 7. SVG Reuse and Semantic Identifiers

Use inline SVG as the first plan surface. SVG `viewBox` supplies the mapping between a drawing's user coordinate space and its viewport. [B2]

Reuse actual geometric primitives from the existing SVG exporter. Do not build the HTML plan by reading an SVG screenshot, tracing an image, or independently reconstructing shapes in JavaScript.

Each selectable rendered entity SHOULD have an association such as:

```xml
<g id="review-existing-main-tree001"
   data-entity-id="TREE001"
   data-layer-id="existing-vegetation">
  <!-- Existing renderer's generated shapes -->
</g>
```

Requirements:

- Entity IDs remain domain identities; DOM IDs identify individual rendered instances.
- Namespace all DOM IDs across scenarios, side-by-side panes, and print views.
- Namespace and rewrite internal references consistently, including marker, pattern, clip-path, mask, symbol, and gradient references.
- Keep label and leader associations so layer changes cannot leave orphan annotations.
- Preserve polygon holes, multipolygons, line geometry, and the renderer's precision policy.
- Treat text position and line-weight presentation separately from physical geometry.

Prefixing SVG IDs with regular-expression substitutions alone is not sufficient if references can become inconsistent. Prefer generating scoped IDs directly or using structured XML processing.

An existing SVG containing an entire sheet may be embedded unchanged for the first release. Extract a reusable plan viewport only when it is needed for interaction or comparison and can be done without destabilizing sheet output.

## 8. Coordinates, Camera, and Measurement

### 8.1 One coordinate contract

Document the exact mapping among:

```text
source/world coordinates -> SVG plan coordinates -> viewport/client coordinates
```

Do not assume SVG user units are feet or that SVG's downward Y direction matches the domain's upward Y direction. Include translations, scaling, rotation, and nested transforms. Define north orientation unambiguously from the actual model.

A browser implementation can invert the appropriate SVG element's screen transformation matrix to map pointer coordinates into that element's coordinate space. [B3] If that space is not already world space, apply the documented inverse world-to-SVG transform as well.

### 8.2 Camera behavior

Provide fit-to-property, zoom in/out, and pan. Constrain extreme zoom and prevent the plan from becoming irretrievably lost. Keep a reset action available.

For scenario comparison, derive one world-coordinate camera and map it into each viewport. Do not synchronize raw CSS pixel offsets. Use shared bounds across compared plans so an unchanged house does not appear to move when options switch.

### 8.3 Ruler, after the basic viewer

A two-point ruler MAY be added in H2. It MUST:

- Compute distance in world units, not screenshot pixels.
- Label freehand measurements as approximate and identify whether snapping is active.
- Remain correct after pan, zoom, browser resizing, Y inversion, and plan rotation.
- Distinguish source accuracy from numerical precision.
- Never substitute for exported, geometry-derived dimensions or surveying.

Test with a 3-4-5 triangle and a rotated/non-unit-scale fixture. Defer area-drawing tools and advanced snapping until there is a real need.

## 9. H1 Viewer Experience: One Useful Plan

The first deliverable MUST contain only the available, validated existing-conditions snapshot or one explicitly selected design snapshot.

Include:

- A plan viewport with clear title, orientation, legend, and source-status notice.
- Pan/zoom/fit controls and named layer checkboxes.
- A searchable entity list and an inspector linked to plan selection.
- Entity ID/type, known measurements, source/confidence, and applicable warnings.
- Project-wide validation summary and missing-information notice.
- A readable static overview when JavaScript is disabled.

Do not add placeholder “AI design,” fake costs, nonfunctional phase sliders, or fabricated scores to make the report appear complete. Unsupported capabilities should be absent or explicitly identified as unavailable.

Layer visibility is presentation only. A hidden lawn layer does not reduce the plan's total lawn area. Any visible-only summary must be named and distinguished from whole-plan totals.

The entity list must remain usable when small features overlap or are difficult to select. Decorative overlays should not steal pointer events from features underneath them.

## 10. H2 Viewer Experience: Compare Meaningful Alternatives

Implement this only after the existing concept resolver is verified or the necessary minimal resolver work is complete.

Require:

- Existing-conditions reference plus available concepts; never fabricate three concepts.
- One-click switching with a common coordinate frame.
- Side-by-side comparison with optional synchronized navigation once single-view switching works.
- A difference summary: added, removed, retained, and modified entities.
- Comparable known metrics with units and documented calculation scope.
- Stable entity selection where the same ID exists in both views; a clear “not present in this option” message otherwise.

Useful early metrics include lawn area, new hardscape area, planting-bed area, retained/removed/new tree counts, and known intervention quantities. These can aid discussion without introducing unverified environmental simulation.

Do not equate net added hardscape area with construction quantity. Replacing an existing patio may involve demolition and full replacement even if the total area is unchanged.

Qualitative owner scores may be shown separately from measured quantities. Show their provenance, weights, direction, and rationale. Unknown shade, water-use, or maintenance values MUST NOT become zeros or invented numeric scores.

The browser should display precomputed results. Reweighting subjective scores may be added later as explicitly labeled review-state arithmetic; it must not change the canonical decision record without an accepted source-data update.

## 11. H3 Viewer Experience: Multi-Year Implementation

A phase view must display the **cumulative resolved site state** after a phase, not merely toggle objects tagged with that year.

The core must distinguish:

```text
baseline retained features
removal/demolition events
new installation events
modifications to existing features
temporary works
phase dependencies
```

For example, an existing bed removed in Phase 2 remains visible through Phase 1 and is absent afterward. A new patio installed in Phase 2 remains visible in later phases. Ordering must follow explicit dependency/sequence rules, not alphabetical IDs or calendar labels alone.

Show phase scope, cumulative state, phase cost, cumulative cost, known prerequisites, and unresolved decisions when that data exists. Evaluate rework using actual overlapping construction scopes and dependencies; a warning should explain the affected geometry and the assumption behind it.

**Construction state and plant growth are different timelines.** Do not animate canopy growth merely by advancing a construction-phase selector. Growth modeling remains a separate, assumption-labeled future feature.

Precompute only explicitly requested, valid scenario/phase combinations. Do not create an unbounded Cartesian product of every scenario, date, analysis, and rendering style.

## 12. Cost and Quantity Honesty

Use existing authoritative quantity and estimate modules if present. If absent, the first viewer should show unknown costs rather than building a speculative estimator as a prerequisite.

When estimates are introduced, require:

- Itemized scope and quantity, not merely the net geometric difference between snapshots.
- Unit-cost provenance, location applicability, date, and currency.
- Low/base/high ranges with clear inclusions and exclusions.
- Explicit labor, materials, demolition, mobilization, design, tax, and contingency treatment where applicable.
- Consistent base-year versus future-year cost treatment for phasing.
- A distinction between owner-supplied allowance, example value, vendor quote, and calculated estimate.

Do not label a scenario range as a statistical confidence interval without a supporting uncertainty model. Do not display example prices as current Trophy Club prices.

Require reconciliation tests so the inspector, comparison report, CSV, and phase totals agree for the same snapshot and scope. Maintain existing financial rounding conventions; avoid introducing competing Python and JavaScript monetary calculations.

## 13. Real-Site Data Before More Abstraction

Promote a usable intake workflow alongside the HTML viewer. A beautiful viewer cannot correct an unmeasured site.

The initial project-ready checklist should cover parcel/survey references, building footprint, major hardscape, fences/gates, existing trees, main access points, utility/service clearances, drainage observations, and photographic coverage. Track what is known, estimated, outdated, or missing.

For each important measurement, preserve its source reference, observation date where known, method, confidence, and any explicit uncertainty. Do not automatically convert a qualitative “high confidence” into a numeric survey tolerance.

A source-quality overlay or inspector badge is valuable early. It helps answer “what do we need to measure next?” before a design depends on an estimate.

Do not populate the real project with the synthetic 80-by-130-foot fixture and imply it is the homeowner's parcel. If foundational geometry is absent, either block a site-accurate export or produce an explicitly requested schematic with a prominent **SCHEMATIC — NOT SITE ACCURATE** notice.

Prioritize real-site input needed to answer the next design question. A basic manual coordinate-entry/calibration workflow may be enough; photogrammetry, survey OCR, advanced terrain modeling, and automatic plant identification are not prerequisites.

## 14. Safe Single-File Packaging

Generate a conventional HTML document with inline CSS, generated SVG, safely embedded data, and an inline bundled script. Keep maintainable templates and JavaScript source files separate in the repository; combine them only during export.

An inert JSON block is an appropriate transport:

```html
<script type="application/json" id="landscape-review-data">
  { "viewer_schema_version": 1 }
</script>
```

Read the block's text and parse JSON. Do not interpolate project content into executable JavaScript, use `eval`, or concatenate untrusted strings into HTML.

### 14.1 Escaping is mandatory

A non-executable JSON script block still sits inside HTML parsing rules. The serializer must prevent project text containing closing script tags from terminating the block. Escape literal `<` in the serialized JSON, with tests for mixed-case closing tags; apply a deliberate policy for `>`, `&`, and Unicode separators. Do not assume generic HTML entity escaping is the correct JSON-script encoding. [B4]

Use safe text insertion for names, notes, captions, and inspector values. Context-sensitive encoding and safe DOM sinks remain necessary; a content security policy is additional protection, not a substitute. [B5]

### 14.2 Allowed assets

For H1, allow only application-generated SVG plus reviewed raster media formats. Do not inline arbitrary uploaded SVG/HTML, scripts, event-handler attributes, remote references, or embedded foreign documents. Imported diagrams requiring display should pass a defined sanitization/conversion process first.

Avoid runtime dynamic imports, worker scripts, or service-worker installation for the standalone viewer. Use one bundled script if a build system is already present; otherwise a small maintained vanilla-JavaScript runtime is sufficient.

### 14.3 Content security policy

Generate and test a restrictive meta-delivered CSP using hashes for the exact trusted inline scripts/styles, and deny connection, object, and form actions. Prefer class and SVG-attribute updates over injected style or event-handler strings. The browser documentation describes meta-delivered CSP and inline hash authorization. [B6]

Do not broaden policy to arbitrary inline execution simply to silence console errors. Verify the policy on actual `file://` exports in target browsers. Document any directive limitations of meta delivery rather than pretending they are response headers.

## 15. Privacy and Sharing Profiles

A self-contained file carries every embedded datum with it. Hiding a panel is not a privacy boundary.

Define a small build-time export profile, with the default intended for sharing:

| Profile | Intended content |
|---|---|
| `share` | Plan geometry, necessary labels, quantities, warnings, and explicitly approved media; exclude unnecessary personal/source information. |
| `private` | Additional approved references or notes, still with a manifest of included content. |

For `share`, exclude street address by default, private contact details, internal notes, source PDFs, raw survey scans, absolute file paths, and exact geographic coordinates unless specifically included. Local plan geometry remains visible and may itself be identifying; do not label the result anonymous.

Apply filtering **before** embedding data, SVG labels, hidden templates, media, and metadata. A field absent from the visible title block but present in the payload has not been removed.

For media, use bounded-resolution derivatives, strip unnecessary metadata, and record which images were embedded. Avoid shipping the entire photo/survey archive. Preserve full originals separately in the project.

Test with synthetic private “canary” strings that must not appear anywhere in a share-profile file. Publishing exports or project media to GitHub or another service is a separate user decision, not an automatic output step.

## 16. Review Comments and Persistence: Optional H4

Do not make browser storage the authoritative home for comments or design changes. In particular, `localStorage` behavior for `file:` documents is undefined and varies by browser; it can also be unavailable. [B7]

A portable feedback workflow may instead be:

```text
Open review.html
  -> attach comment to an entity or world-coordinate location
  -> download review-notes.json
  -> import notes through the trusted project workflow
  -> validate source revision and references
  -> human review
```

Each note should include project identity, source/snapshot digest, scenario, phase, entity reference when relevant, original anchor coordinate if relevant, and comment text. A content hash establishes correspondence, not reviewer identity or authenticity.

When importing against another revision, report stale references and changed geometry. Do not silently relocate old comments to a newly positioned entity or treat a comment as an approved design operation.

Use explicit user-selected file input for importing feedback; the File API supports reading files the user selects. [B8] Export a new file rather than promising to overwrite the original HTML or canonical YAML silently. Optional convenience caching must fail safely and be visibly distinguished from a saved review file.

H4 is not required for H1 or H2. Full collaborative editing, authentication, merge resolution, and persistent browser CAD remain out of scope.

## 17. Reproducibility Contract

Separate computational determinism, generated-file determinism, and visual consistency.

**Computational:** The same validated source, configuration, and pinned toolchain produce the same resolved geometry and values.

**Artifact:** The same source, export profile, selected snapshots, templates, runtime bundle, and pinned toolchain produce identical HTML bytes under reproducible settings.

**Visual:** The same design and data remain consistent across supported browsers. Do not promise pixel-identical typography across operating systems or browser versions when using system fonts.

To implement this:

- Sort only collections whose order is semantically irrelevant; preserve explicit layer and operation order.
- Use stable IDs, JSON formatting, number formatting, resource ordering, and SVG serialization.
- Do not round canonical source coordinates merely to stabilize a screenshot.
- Compute a stable source/snapshot digest with a documented scope.
- Exclude wall-clock build time from reproducible HTML, or accept an explicit fixed timestamp as an input.
- Keep volatile build logs outside the artifact or disclose them as a deliberate reproducibility exception.
- Record exporter version, viewer schema version, and relevant source revision without leaking private paths.

A manifest MUST distinguish code revision from project-data revision. Two exports produced by the same software commit may contain different property designs.

## 18. Printing and Existing Professional Outputs

Retain SVG and any working PDF/DXF exporters. HTML is not a reason to rebuild established professional-output pipelines.

Provide a print stylesheet with a fixed review layout, selected snapshot title, legend, revision, and assumptions. Hide interactive controls and ensure print output shows a known plan view rather than whichever zoomed corner happened to be visible. CSS print media and page rules can define print-specific presentation. [B9]

Screen zoom and physical drawing scale are different. Label the interactive view **screen scale varies**. Include a coordinate-derived graphic scale that remains attached to the drawing, and a ruler/verifiable scale reference in fixed-size sheet exports.

Do not guarantee calibrated contractor print scale from arbitrary browser “Print” settings. Designate the existing fixed-page vector output as the controlled scaled deliverable, subject to printing at the documented size and checking the scale reference. HTML review printing is a convenience unless a separate print-validation process has been completed.

Do not label homeowner-generated drawings as sealed, surveyed, engineered, or construction-approved. Show conceptual status and review requirements at relevant locations rather than hiding them in fine print.

## 19. Accessibility and Usability Requirements

Use native buttons, checkboxes, inputs, headings, and tables where possible. Provide labels, keyboard operation, visible focus, and an entity list as an alternative to mouse-only SVG selection.

Warnings and existing/proposed/demolished status must not rely solely on color. Combine text, line style, symbols, and an intelligible legend. Avoid hover-only details and unnecessarily animated transitions.

At minimum, manually test keyboard-only use, high zoom, long labels, narrow layout, an empty search result, unknown measurements, and a very small selected feature. A static default plan should remain available if interactive initialization fails.

## 20. Performance and Export Budgets

Set initial budgets as **proposed targets to measure**, not statements about current performance:

| Fixture | Proposed initial budget |
|---|---|
| Four snapshots, up to 1,000 feature instances each, no photo archive | Export at or below 5 MiB |
| Core opening and first useful interaction | Within 2 seconds on a documented reference laptop/browser |
| Ordinary toggle/selection response | Within 100 ms on that reference fixture |
| Media-heavy exports | Explicit warning above a configurable size budget |

Record hardware, browser version, fixture, and measurement method. Adjust budgets through an ADR when a measured real-site need justifies it.

Avoid duplicating full source geometry in both SVG and JSON unless an interaction requires it. Inspector metadata generally needs identifiers, values, and references rather than a second copy of every vertex.

Start with a small number of pre-rendered snapshots. If size becomes a demonstrated issue, reuse generated components or lazily attach already-embedded content. Do not solve a hypothetical large-project problem with a remote API or a browser geometry rewrite.

## 21. Error Handling and Backward Compatibility

Export MUST fail clearly for invalid authoritative geometry or broken required references, following existing validation policy. A request for HTML must not bypass validation that other formats perform.

Unimplemented optional data should yield an absent/unavailable feature, not an export failure unless that feature was explicitly requested. Missing required assets must be reported; they must not trigger an undisclosed remote download.

Write exports atomically so a failed render does not leave a misleading half-written artifact. Honor existing overwrite conventions and protect project inputs.

Keep old commands and default formats working. Introducing HTML alone should not require a project-schema migration. Add only the optional metadata actually needed, with compatibility tests and migrations if a real breaking change is unavoidable.

## 22. Proposed CLI Contract

Extend the real CLI rather than introducing a second executable. If its conventions match the original proposal, a suitable shape is:

```bash
# Proposed syntax, not verified repository commands.
uv run landscape render projects/greenleaf \
  --format html \
  --sheet existing \
  --profile share \
  --output generated/greenleaf-review.html
```

Later, where corresponding capabilities exist:

```bash
# Proposed syntax: adapt to the actual concept and phase model.
uv run landscape render projects/greenleaf \
  --format html \
  --scenario existing,concept_a,concept_b \
  --profile share \
  --output generated/greenleaf-options.html
```

A file exported as standalone HTML should be standalone by default; do not require a hidden “offline mode” flag. Keep scenario selection explicit and bounded. Document source data, included snapshots, warnings, and output size in the CLI result.

Do not invent successful command output or mark these commands implemented before executing their actual counterparts.

## 23. Required Acceptance Tests

Use the existing test framework and add browser tests only where necessary. Playwright supports request observation and interception, including request abortion, which can help verify network independence. [B10] Browser test tooling is a development dependency, not a recipient requirement.

These are requirements for the coding agent; **none of the repository tests below have been executed during preparation of this document**.

### 23.1 H1 release gates

| ID | Test | Passing behavior |
|---|---|---|
| HTML-001 | Export a validated synthetic project | One complete HTML file and no required companion directory. |
| HTML-002 | Copy only the file into a new temporary directory | All advertised core features still work. |
| HTML-003 | Open the copied file via `file://` with networking disabled | Default plan, controls, layers, and inspector function; no runtime errors. |
| HTML-004 | Record resource/network activity | No application-initiated remote requests or unapproved external dependencies. |
| HTML-005 | Disable JavaScript | A readable default plan, title, assumptions, and summary remain. |
| HTML-006 | Select a feature from plan and entity list | Both select the same entity and display matching source data. |
| HTML-007 | Toggle a layer | Associated geometry and labels change visibility; whole-plan totals do not change. |
| HTML-008 | Compare with existing SVG export | The same snapshot has equivalent geometry, units, dimensions, and relevant styles; scoped DOM IDs may differ. |
| HTML-009 | Hostile text fixture | Quotes, ampersands, closing-script strings, and markup appear as text; no injected code executes. |
| HTML-010 | Private canary fixture | Share-profile output excludes private strings and data from visible and embedded content. |
| HTML-011 | Repeat a reproducible build | Identical inputs and pinned toolchain produce identical HTML bytes. |
| HTML-012 | Invalid geometry or broken references | Clear validation failure; no silently accepted or partially written plan. |
| HTML-013 | Existing regression suite | Existing commands and output formats continue to satisfy their contracts. |
| HTML-014 | CSP enforcement | Trusted interactions work and untrusted fixture content does not require policy weakening. |
| HTML-015 | Unknown measurements | UI says unknown/estimated as appropriate; no invented values or implied survey accuracy. |

Open files with an actual `file://` navigation in tests, not only through a test server or an in-memory HTML insertion API. Use both source/resource inspection and runtime checks: absence of successful network responses alone does not prove the file never attempted requests.

Record tested browsers and versions. A Chromium-only pass is not a Safari/Firefox certification. Inspect at least one exported plan manually for label overlap, clipping, hierarchy, useful selection, and source-status visibility.

### 23.2 H2 comparison and ruler gates

| ID | Test | Passing behavior |
|---|---|---|
| COMP-001 | Switch among baseline and available concepts | Shared retained features remain in the same world position. |
| COMP-002 | Side-by-side views with different viewport sizes | Camera synchronization uses world coordinates; no apparent design displacement. |
| COMP-003 | All included SVG instances | Unique DOM IDs and correct internal SVG references. |
| COMP-004 | Change concept while inspecting an entity | Inspector shows that snapshot's data or explicitly reports absence. |
| COMP-005 | Compare quantities | Viewer values reconcile with core reports for the same scope. |
| COMP-006 | Retain baseline and source hashes before/after interaction | No project-state mutations. |
| MEAS-001 | Measure a 3-4-5 fixture | Correct world-space distance within declared numeric tolerance. |
| MEAS-002 | Repeat with Y inversion, non-unit scale, rotation, pan, zoom, and resize | Same result; pointer mapping remains correct. |
| COMP-007 | Missing metric or qualitative score | Explicit unknown/qualitative treatment; no misleading total. |

### 23.3 H3/H4 future gates

Require cumulative phase-state correctness, dependency validation, cost-scope reconciliation, and explicit separation of installation timing from plant maturity. Include at least one install-then-remove fixture that produces an explainable rework warning.

For feedback, test export/import round trips, unknown IDs, stale source digests, relocated entities, Unicode notes, storage exceptions, and no silent source-file writes.

### 23.4 Testing discipline

Use structural tests for semantics and a small set of browser screenshots for visual regressions. Do not substitute pixel snapshots for coordinate/quantity tests. Pin browser versions used for visual baselines and document intentional changes.

A test omitted because tooling is unavailable is **not run**, not passed. Do not update golden files to suppress an unexplained regression.

## 24. Incremental Delivery Plan

### H0 — Verified baseline and implementation map

Deliver the actual `main` audit, command results, inspected output, and an ADR defining the smallest HTML integration point. Identify existing work to preserve and any prerequisite defects. This step is mandatory because repository review was blocked when this addendum was drafted.

**Exit:** Every claim about current progress has evidence or an explicit unknown status; the next patch has concrete files and acceptance tests.

### H1 — Portable single-plan review file

Implement safe packaging, reused SVG, required metadata, pan/zoom/fit, layers, linked entity inspection, no-JavaScript fallback, default privacy filtering, and offline/regression tests.

**Exit:** Copying one file to another folder and opening it without networking produces a useful, accurate review of the supplied snapshot.

Do not include a concept engine rewrite, full editor, solar engine, 3D renderer, live database, or cost-system invention in H1.

### H2 — Alternatives and inspection tools

Connect verified concept snapshots, comparable quantities, a difference summary, stable switching, and then synchronized comparison. Add a two-point ruler only after the coordinate contract is tested.

**Exit:** The homeowner can explain meaningful differences between at least two deliberately authored alternatives for a validated fixture; use real-property alternatives once sufficient real data exists.

If concepts are not implemented, identify and complete the smallest deterministic concept-resolution prerequisite rather than simulating it in the browser.

### H3 — Phased execution review

Connect cumulative phase snapshots, source-backed cost ranges where available, prerequisites, and rework explanations. Keep estimated or missing information explicit.

**Exit:** The user can answer “what exists after this phase, what does this phase change, and what should precede it?” without confusing future plant growth with construction state.

### H4 — Review feedback and refinement

Add optional portable comments, approved photo callouts, and focused usability improvements driven by actual homeowner/contractor review sessions.

**Exit:** Feedback returns with traceable context and cannot silently become an authoritative design modification.

A full browser authoring application requires a separate design decision. It is not the automatic next milestone after H4.

## 25. Documentation and Progress Reporting Changes

Keep `PROJECT_PROGRESS.md` concise and evidence-led rather than copying the entire product roadmap into it.

For each completed item, record:

```text
capability and scope
implementation commit
relevant paths
verification commands
last verified date and outcome
representative artifact or screenshot
known limitations
next blocking dependency
```

“Implemented,” “tests passed,” “visually reviewed,” and “validated against the real property” are different claims. Record them separately.

Update the original specification with a short link/reference to this adopted addendum and the precise sections it supersedes. Keep a compact acceptance matrix for the active milestone; move speculative future features out of the immediate task list.

Do not claim a feature works because its class exists, because a stub CLI command runs, or because an example output was committed without a reproducible generation path.

## 26. Specific Corrections to the Earlier Conversation Specification

These are critiques of the **earlier conversation proposal**, not findings about the inaccessible repository version.

1. **Promote interactive review without committing to a full editor.** “No GUI initially” was too broad for the homeowner's sharing and comparison needs. A read-only generated viewer is a different scope from CAD authoring.
2. **Reconcile timestamps with deterministic output.** A new wall-clock timestamp in every generated file conflicts with a byte-identical-output goal unless it is an explicit input or excluded from that guarantee.
3. **Treat the real base plan as a product dependency.** The synthetic fixture is a software test, never evidence that the homeowner's parcel or structures have been captured correctly.
4. **Separate drawing quality from technical authorization.** Professional-looking linework does not establish surveyed boundaries, code compliance, engineering adequacy, or construction readiness.
5. **Keep unverified measurements and local rules unknown.** An estimate or unsourced local restriction should not become a hard constraint merely because it can be represented in YAML.
6. **Make progress outcome-based.** Fewer well-verified features that let the family make a landscape decision are more useful than a large number of nominally implemented sections.

These changes preserve the original project's purpose while giving the coding agent a smaller and more demonstrable next target.

## 27. Immediate Coding-Agent Assignment

Use the following instruction after adding this document to the repository:

```text
Read repository instructions, LANDSCAPE_PLANNER_SPEC.md,
PROJECT_PROGRESS.md, and LANDSCAPE_STANDALONE_HTML_SPEC.md.

This addendum was prepared without access to current main. Do not treat it
as a completed code review or assume its suggested paths already exist.

First complete H0:
- Record the exact main revision being inspected and workspace status.
- Read the actual model, renderer, CLI, exporters, tests, and examples.
- Run documented verification commands and inspect representative output.
- Produce an evidence-based progress review and a minimal integration map.

Then implement only H1 and any demonstrated prerequisite fixes:
- Reuse the existing geometry and SVG pipeline.
- Produce one self-contained, read-only HTML file.
- Include layers, pan/zoom/fit, entity inspection, clear provenance,
  safe data embedding, privacy filtering, and a static fallback.
- Prove it works after copying the file alone and opening through file://
  with networking disabled.
- Preserve existing commands, outputs, project data, and tests.

Do not build a full editor, rewrite working architecture, duplicate geometry
calculations in JavaScript, fabricate missing site data, or mark unavailable
tests as passed.

Finish with the inspected commit, files changed, verification results,
a representative generated artifact, remaining limitations, and the next
smallest useful implementation step. Update progress documentation using
verified evidence only.
```

## 28. Success Criteria

This workstream succeeds when a portable file supports the homeowner's real decisions while retaining the project's deterministic foundation:

> Which parts of this plan are measured versus estimated? What changes between options? What will the yard contain after each phase? What information or professional review do we still need before spending money?

The standalone file is successful because those answers are inspectable and traceable—not because the viewer looks like a sophisticated application.

## 29. Evidence and Technical References

### Repository review status

The requested targets were:

```text
https://github.com/niederee/landscape
https://github.com/niederee/landscape/blob/main/LANDSCAPE_PLANNER_SPEC.md
https://github.com/niederee/landscape/blob/main/PROJECT_PROGRESS.md
```

These URLs identify the requested material; they are **not citations to inspected repository contents**. Retrieval was unsuccessful. Current implementation state, dependency versions, test results, and progress claims remain unverified in this document.

The original 105-section specification in this conversation supplied the project intent and proposed architecture. It was used only as design context, not as evidence of what has been built.

### Browser and testing documentation

The following documentation was consulted on September 5, 2026. It supports browser behavior and implementation constraints, not any claim about this repository's implementation. Proposed product priorities, numeric performance budgets, module boundaries, and acceptance tests are recommendations in this document.

**[B1] MDN — Reason: CORS request not HTTP.** Local-file origin behavior and CORS-dependent requests.  
`https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSRequestNotHttp`

**[B2] MDN — SVG viewBox.** Coordinate-space and viewport mapping.  
`https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/viewBox`

**[B3] MDN — SVGGraphicsElement.getScreenCTM().** SVG coordinate transformation matrices.  
`https://developer.mozilla.org/en-US/docs/Web/API/SVGGraphicsElement/getScreenCTM`

**[B4] WHATWG — HTML Standard, restrictions for contents of script elements.** Script-element parsing and escaping considerations.  
`https://html.spec.whatwg.org/multipage/scripting.html#restrictions-for-contents-of-script-elements`

**[B5] OWASP — Cross Site Scripting Prevention Cheat Sheet.** Context-sensitive output encoding and safe insertion.  
`https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html`

**[B6] MDN — Content-Security-Policy.** Meta-delivered policies and hash-based authorization of inline content.  
`https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy`

**[B7] MDN — Window.localStorage.** Undefined `file:` behavior and storage-access exceptions.  
`https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage`

**[B8] MDN — Using files from web applications.** User-selected files and browser File API access.  
`https://developer.mozilla.org/en-US/docs/Web/API/File_API/Using_files_from_web_applications`

**[B9] MDN — Printing.** Print stylesheets and page-specific presentation.  
`https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing`

**[B10] Playwright Python — Network.** Request observation, interception, and blocking for browser verification.  
`https://playwright.dev/python/docs/network`
