# From a site inventory to alternatives and phases

Keep the existing-conditions project as the baseline. Author alternatives and
construction phases in a separate `planning.yaml`; the Python resolver produces
new snapshots without rewriting the baseline. The HTML files are portable review
outputs, not editors or construction approval.

For an actual property, begin with [Site capture](SITE_CAPTURE_GUIDE.md). The
checked-in Greenleaf geometry is still provisional. The following demonstration
uses only the explicitly synthetic site.

## Run the demonstration

From the repository root with dependencies installed:

```bash
uv run landscape validate examples/synthetic
uv run landscape compare examples/synthetic
uv run landscape phases examples/synthetic
```

The comparison command reads `examples/synthetic/planning.yaml`, resolves the
baseline and both authored alternatives, and exports one HTML review. The phases
command resolves cumulative construction snapshots from the same planning file.
Each command prints its output path. Copy only the resulting HTML file to another
folder and open it in a browser; source YAML and images are not required there.

Use `--planning /path/to/planning.yaml` to choose a different planning document,
`--output /path/to/review.html` to choose the destination, or `--profile private`
for an owner-only review. The default profile is `share`; geometry and labels
remain identifying information, so inspect the output before sending it.

| Synthetic option | Deliberately authored tradeoff |
|---|---|
| `gathering` | Enlarge the existing patio and reduce lawn; preserve `TREE001` |
| `garden` | Keep the existing patio and convert part of the lawn to an additional bed |

These options demonstrate different uses of the same space. They are not an
automated recommendation, a plant palette, a real-property design, or a budget.
Read individual quantity categories separately: overlapping categories cannot be
summed into a trustworthy parcel-coverage total.

## Author an alternative

The optional planning file has its own schema version:

```yaml
schema_version: 1
concepts:
  - id: retain_tree
    name: Retain the established tree
    operations:
      - action: preserve
        category: trees
        entity_id: TREE001
phases: []
```

Supported categories are `structures`, `hardscape`, `linear_features`, `trees`,
`planting_beds`, `lawn`, and `utilities`. The parcel and coordinate frame are
shared by every alternative. Define operations in their intended execution order.

| Action | Meaning | Required data |
|---|---|---|
| `add` | Introduce an entity with a new stable ID | `data` matching the category's entity schema; ID is injected or must match |
| `update` | Replace selected top-level fields of an existing entity | `data` containing the replacement fields |
| `remove` | Remove an existing entity from the resulting snapshot | No `data` |
| `preserve` | Retain an entity and prevent subsequent changes in the operation sequence | No `data` |

An update replaces a nested field as a whole. For example, changing `geometry`
requires its complete type and coordinate data; changing `source` replaces that
source block. A source on a proposed dimension should describe the design input,
not imply the proposed object was measured on site. Use `status: proposed`
explicitly when authoring new or changed design features.

All IDs remain unique. A missing target, invalid replacement, conflicting
preservation or invalid resolved geometry fails clearly. Core validation warnings
remain review items. The baseline does not change when a concept is resolved, and
one alternative does not inherit another alternative's edits.

Start real alternatives with one written homeowner priority each, using the
private program notes: desired activities, first area, maintenance tolerance,
annual spending range and DIY/contractor preference. Those preferences do not
automatically generate geometry or an objective numerical design score.

## Select a target and author cumulative phases

Set `selected_concept` to an authored concept ID once choosing a target. The
synthetic file selects `gathering`. Its first phase changes the affected lawn;
the second depends on that preparation and expands the patio. The final phase
must equal the selected concept's existing-conditions snapshot or the CLI rejects
the export. This prevents a successful-looking phase review for a different plan.

A phase has `id`, `name`, optional `depends_on`, `operations` using the same
contract as concepts, and optional `cost_items`. Phases start from existing
conditions and accumulate in dependency order. Among phases whose prerequisites
are satisfied, the earliest in the authored list runs next. A snapshot includes
**all** earlier phases, including independent branches; dependencies do not
select alternative timelines. Unknown dependencies, cycles and duplicate phase
IDs fail validation.

Preservation continues across phases. Installing a feature and later changing or
removing it produces a potential rework warning for review. These warnings do not
estimate demolition labor or prove the sequence is practical. Phase IDs and names
describe installation sequence; they are not dates, plant ages or mature-growth
simulations.

## Estimate only what has a source

The synthetic example intentionally omits unit rates. Its preparation and patio
line items are **unknown costs**, not free work.

A cost item contains `id`, optional `name`, `quantity`, `unit`, `currency` (USD),
and optional `rate_low`, `rate_high` and `source`. Both rates must be supplied together, be
nonnegative and ordered, and have a nonblank source. Quantities and extended
costs must be finite. Leave both rates absent if there is no usable quote or
allowance. Record the supplier/document/date and scope in the private source
material; a source string alone is not independent price verification.

This initial model accepts USD only and does not convert currencies.
Known low/high subtotals sum only the supplied priced line items.
The software reports unknown items separately and flags an operation-bearing
phase with no cost items as unestimated. A complete supplied list does not prove
the entire job is priced: explicitly consider demolition, preparation, disposal,
labor, material delivery and exclusions when preparing the actual scope.

Geometry-derived net area changes and installation quantities answer different
questions. An existing patio replacement could have zero net area change and
substantial installation work. Item quantities are authored scope inputs, not
automatically verified takeoffs or contractor quotes.

## Review and remaining boundaries

Review the baseline, both alternatives and each cumulative phase. Check retained
feature positions, quantities, absent/removed features, warnings and sources.
Keep an explicit list of decisions and unresolved information outside the source
geometry until the owner accepts a revision.

The software work can proceed with synthetic fixtures independently of survey
delivery. A trustworthy Greenleaf plan still needs actual source capture,
homeowner decisions and review of affected site constraints. This workflow does
not yet produce dimensioned construction details, a verified planting schedule,
seasonal shade/drainage analysis, automatic design generation or portable
feedback import. Browser verification applies only to the browsers actually run;
an offline HTML artifact is not certification of Safari/Firefox compatibility.
