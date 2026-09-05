# Landscape Planner

## Deterministic Residential Landscape Architecture Planning System

**Status:** Initial specification  
**Reference project:** Residential property in Trophy Club, Texas  
**Primary user:** Homeowner / software developer  
**Primary objective:** Produce professional-quality, multi-option, multi-year residential landscape master plans using deterministic geometry, structured data, reproducible analysis, and high-quality vector drawings.

**Delivery direction (September 5, 2026):** See
[`docs/PROJECT_DIRECTION_REVIEW.md`](docs/PROJECT_DIRECTION_REVIEW.md) for the
repository audit and outcome-based roadmap. Adopt
[`LANDSCAPE_STANDALONE_HTML_SPEC.md`](LANDSCAPE_STANDALONE_HTML_SPEC.md) for output
priorities, read-only viewer scope, and viewer acceptance criteria. It supersedes
the original output sequencing and any interpretation of “no GUI initially”
that would exclude a generated review document. The structured model and
deterministic geometry principles below remain authoritative.

---

# 1. Product Vision

Build a deterministic software system for planning residential landscapes.

The system should allow a homeowner, designer, landscape architect, contractor, or AI-assisted design workflow to:

1. Model an existing residential property accurately.
2. Record known and uncertain site conditions.
3. Analyze environmental and functional constraints.
4. Develop multiple genuinely different landscape concepts.
5. Compare those concepts objectively.
6. Select or combine concepts into a master plan.
7. Produce multi-year implementation phases.
8. Calculate quantities and approximate costs.
9. Produce professional-quality plan sheets.
10. Reproduce every drawing and calculation from structured source data.

The software must distinguish between:

- measured facts,
- imported survey information,
- observed conditions,
- assumptions,
- design decisions,
- estimates,
- generated analysis.

The application must not behave like a generative image tool.

The core principle is:

> **Structured property data → deterministic calculations → deterministic drawings**

AI may assist with interpretation, design reasoning, suggestions, descriptions, or proposed changes, but AI must never be the authoritative source of geometry.

---

# 2. Core Design Philosophy

The system should follow several principles.

## 2.1 Determinism

Given identical project data and identical software versions:

```text
project data
    ↓
geometry engine
    ↓
analysis engine
    ↓
rendering engine
    ↓
identical outputs
```

The same input must produce the same:

- coordinates,
- areas,
- lengths,
- quantities,
- scores,
- drawings,
- cost calculations.

---

## 2.2 Single Source of Truth

The structured project files are authoritative.

Generated artifacts such as:

- SVG,
- PDF,
- DXF,
- CSV,
- HTML,

must never become the primary project data.

They are outputs.

A user should be able to delete every generated artifact and rebuild the entire drawing package from source data.

---

## 2.3 Human-Readable Project Files

Project data should be stored in human-readable formats whenever practical.

Preferred initial format:

```text
YAML
```

The homeowner should be able to inspect and edit the project without a proprietary application.

Example:

```yaml
trees:
  - id: T001
    species: Quercus virginiana
    common_name: Live Oak
    location: [42.5, 63.8]
    trunk_diameter_in: 14
    canopy_radius_ft: 17
    disposition: preserve
```

---

## 2.4 Geometry Before Rendering

The rendering layer must not contain landscape-design logic.

Bad:

```python
draw_circle(42, 63, 17)
```

with no underlying tree entity.

Good:

```python
tree = project.trees["T001"]
renderer.draw(tree)
```

Geometry calculations belong in the model and analysis layers.

Rendering only visualizes the resulting data.

---

## 2.5 Professional Workflow

The software should reflect the general sequence used in professional site planning:

```text
Existing Conditions
        ↓
Site Analysis
        ↓
Program / Requirements
        ↓
Concept Alternatives
        ↓
Concept Evaluation
        ↓
Master Plan
        ↓
Technical Plans
        ↓
Phasing
        ↓
Implementation
```

Do not begin detailed plant selection before the spatial structure of the landscape has been resolved.

---

# 3. Scope

The initial system is focused on residential landscape master planning.

It should eventually support:

- property boundary
- house footprint
- garage
- driveway
- sidewalks
- patios
- decks
- pools
- fences
- gates
- retaining walls
- existing trees
- shrubs
- planting beds
- lawn
- utilities
- HVAC equipment
- drainage
- irrigation
- exterior lighting
- sun/shade analysis
- views
- privacy
- circulation
- activity zones
- outdoor rooms
- proposed trees
- proposed planting
- hardscape
- outdoor living structures
- project phases
- cost estimates
- plant schedules
- material schedules
- quantity calculations

---

# 4. Non-Goals

The initial application should **not** attempt to replace licensed professionals for work requiring engineering, permitting, stamping, or specialized calculations.

Specifically, do not initially attempt to provide authoritative:

- structural engineering
- retaining wall engineering
- stormwater engineering
- hydraulic calculations
- electrical engineering
- gas-line design
- pool engineering
- foundation engineering
- surveying
- legal property-boundary determination

The system may represent these elements and flag issues requiring professional review.

Example:

```text
WARNING:
Proposed retaining wall exceeds configured homeowner-design threshold.
Professional engineering review recommended.
```

---

# 5. Reference Project

The first real-world implementation will be a residential property in:

```text
Trophy Club, Texas
```

The software must remain generic.

Do not hard-code rules specifically for Trophy Club into the geometry engine.

Local information should eventually be represented through configurable project metadata and rule sets.

Example:

```yaml
jurisdiction:
  city: Trophy Club
  state: TX
  country: US

climate:
  region: north_texas

rulesets:
  - trophy_club_residential
  - north_texas_waterwise
```

The user's actual property will serve as the first reference project and test case.

---

# 6. Technology Stack

Use Python for the core application.

Recommended baseline:

```text
Python 3.13+
uv
pytest
Pydantic
Shapely
PyYAML or ruamel.yaml
Typer
Rich
ezdxf
```

Potential rendering dependencies:

```text
SVGWrite or direct SVG generation
CairoSVG
ReportLab
```

Potential future dependencies:

```text
GeoPandas
Rasterio
Pillow
NumPy
SciPy
Astral / solar-position library
Hypothesis
FastAPI
React or similar web UI
```

Avoid introducing heavy GIS dependencies until they are actually required.

---

# 7. Package Architecture

Recommended repository layout:

```text
landscape-planner/
│
├── pyproject.toml
├── README.md
├── LANDSCAPE_PLANNER_SPEC.md
│
├── src/
│   └── landscape_planner/
│       │
│       ├── __init__.py
│       │
│       ├── cli/
│       │   └── main.py
│       │
│       ├── model/
│       │   ├── project.py
│       │   ├── geometry.py
│       │   ├── site.py
│       │   ├── vegetation.py
│       │   ├── infrastructure.py
│       │   ├── analysis.py
│       │   ├── design.py
│       │   ├── phasing.py
│       │   └── cost.py
│       │
│       ├── io/
│       │   ├── yaml_loader.py
│       │   ├── yaml_writer.py
│       │   ├── dxf.py
│       │   └── migration.py
│       │
│       ├── analysis/
│       │   ├── geometry.py
│       │   ├── site_analysis.py
│       │   ├── shade.py
│       │   ├── drainage.py
│       │   ├── circulation.py
│       │   ├── privacy.py
│       │   ├── scoring.py
│       │   └── validation.py
│       │
│       ├── rendering/
│       │   ├── svg.py
│       │   ├── symbols.py
│       │   ├── annotations.py
│       │   ├── dimensions.py
│       │   ├── sheets.py
│       │   ├── legends.py
│       │   └── styles.py
│       │
│       ├── estimating/
│       │   ├── quantities.py
│       │   └── costs.py
│       │
│       └── utilities/
│
├── projects/
│   └── greenleaf/
│       ├── project.yaml
│       ├── existing_conditions.yaml
│       ├── program.yaml
│       ├── costs.yaml
│       ├── plants.yaml
│       │
│       ├── concepts/
│       │   ├── concept_a.yaml
│       │   ├── concept_b.yaml
│       │   └── concept_c.yaml
│       │
│       ├── master/
│       │   └── master_plan.yaml
│       │
│       ├── references/
│       │   ├── survey/
│       │   ├── photos/
│       │   └── notes/
│       │
│       └── generated/
│           ├── svg/
│           ├── pdf/
│           ├── dxf/
│           ├── csv/
│           └── reports/
│
└── tests/
    ├── unit/
    ├── integration/
    ├── golden/
    └── fixtures/
```

---

# 8. Coordinate System

Use a local Cartesian coordinate system initially.

Default units:

```text
feet
```

Recommended orientation:

```text
+X = east
+Y = north
```

The origin should normally be an obvious stable survey point such as:

```text
southwest property corner = (0, 0)
```

However, the system must support arbitrary origins.

Project metadata must record:

```yaml
coordinate_system:
  type: local_cartesian
  horizontal_units: ft
  origin_description: southwest_property_corner
  north_rotation_degrees: 0
```

Future versions may support geographic coordinates and CRS metadata.

---

# 9. Measurement Provenance

Every significant geometric element should support provenance.

Example:

```yaml
source:
  type: survey
  reference: closing_survey_2023.pdf
  confidence: high
```

Supported source types should include:

```text
survey
field_measurement
gps
aerial
photo_estimate
manual_estimate
contractor_plan
record_drawing
inferred
unknown
```

Confidence:

```text
high
medium
low
```

Optional accuracy:

```yaml
estimated_accuracy_ft: 0.25
```

This distinction is critical.

A surveyed property line must not be treated equivalently to something estimated from a photograph.

---

# 10. Core Geometry Types

The geometry layer should wrap or use Shapely.

Required types:

```text
Point
LineString
Polygon
MultiPolygon
```

All entities should expose relevant calculated values.

Examples:

```python
polygon.area
line.length
polygon.centroid
polygon.bounds
```

Use geometry validation.

Invalid polygons should fail project validation.

---

# 11. Base Entity Model

All model entities should include a common set of fields.

Example:

```python
class Entity:
    id: str
    name: str | None
    description: str | None
    tags: list[str]
    source: SourceInfo | None
    notes: list[str]
```

IDs must be stable.

Examples:

```text
PARCEL001
STRUCT001
TREE001
BED001
FENCE001
PATIO001
ROOM001
```

Do not use array indexes as permanent identifiers.

---

# 12. Site Project Model

The project itself should contain:

```python
LandscapeProject
```

Suggested fields:

```python
project_id
name
site_address
jurisdiction
coordinate_system
parcel
existing_conditions
program
concepts
master_plan
phases
cost_model
drawing_settings
```

Example:

```yaml
project:
  id: greenleaf
  name: Greenleaf Landscape Master Plan

  location:
    city: Trophy Club
    state: TX

  units:
    distance: ft
    area: sqft
```

Exact street-address information should remain project data rather than being embedded into application code.

---

# 13. Parcel

A parcel should contain:

```python
Parcel
```

Fields:

```text
boundary
easements
setbacks
rights_of_way
legal_notes
```

Example:

```yaml
parcel:
  id: PARCEL001

  boundary:
    type: polygon
    coordinates:
      - [0, 0]
      - [80, 0]
      - [80, 130]
      - [0, 130]
```

---

# 14. Structures

Required entity:

```python
Structure
```

Examples:

```text
house
garage
shed
pergola
pavilion
pool_house
```

Properties:

```text
footprint
height
floor_elevation
roof_overhang
doors
windows
use
existing/proposed
```

Doors should be represented because circulation relationships depend on them.

Example:

```yaml
doors:
  - id: DOOR_REAR_KITCHEN
    location: [45.2, 72.3]
    exterior_direction: south
    use: primary_backyard_access
```

---

# 15. Hardscape

Required entity:

```python
HardscapeArea
```

Types:

```text
driveway
sidewalk
patio
deck
pool_deck
gravel
decomposed_granite
stepping_stones
sport_surface
other
```

Properties:

```text
geometry
material
existing/proposed
surface_type
permeable
phase
```

Calculated values:

```text
area
perimeter
estimated_material_quantity
```

---

# 16. Linear Features

Required entity:

```python
LinearFeature
```

Types may include:

```text
fence
retaining_wall
edging
curb
drainage_channel
utility_line
irrigation_main
```

Calculated values:

```text
length
```

---

# 17. Existing Trees

Required model:

```python
Tree
```

Fields:

```text
id
location
species
common_name
trunk_diameter
canopy_radius
height
condition
disposition
evergreen
notes
```

Disposition:

```text
preserve
remove
relocate
evaluate
```

Example:

```yaml
- id: TREE001
  common_name: Live Oak
  species: Quercus virginiana

  location: [42.3, 67.1]

  trunk_diameter_in: 14
  canopy_radius_ft: 16
  height_ft: 32

  condition: good
  disposition: preserve
```

Render existing trees differently from proposed trees.

---

# 18. Planting Beds

Required entity:

```python
PlantingBed
```

Fields:

```text
geometry
light_condition
water_requirement
soil_condition
design_style
irrigation
mulch
existing/proposed
```

Calculated:

```text
area
perimeter
mulch_volume
plant_capacity
```

---

# 19. Lawn

Required entity:

```python
LawnArea
```

Fields:

```text
geometry
species
sun_condition
irrigation
existing/proposed
condition
```

Calculated:

```text
area
```

Lawn should be modeled separately from generic planting beds.

---

# 20. Utilities and Equipment

Model relevant equipment and utilities.

Examples:

```text
HVAC
electric_meter
gas_meter
transformer
cleanout
water_meter
sewer
hose_bib
pool_equipment
generator
downspout
```

Model:

```python
UtilityFeature
```

Fields:

```text
location or geometry
type
clearance_zone
visibility
access_requirement
```

Design validation should prevent proposed elements from blocking required service access.

---

# 21. Drainage

Initial drainage modeling should remain intentionally simple.

Represent:

```text
spot elevations
high points
low points
flow paths
downspouts
drains
swales
known wet areas
erosion
```

Models:

```python
SpotElevation
DrainagePath
DrainageArea
DrainFeature
```

Example:

```yaml
spot_elevations:
  - id: ELEV001
    location: [30, 50]
    elevation_ft: 100.25
```

Do not initially attempt full civil stormwater modeling.

The system may derive approximate slope:

```text
slope = elevation_difference / horizontal_distance
```

Drainage output should clearly distinguish between:

```text
observed
calculated
conceptual
engineered
```

---

# 22. Irrigation

Represent existing and proposed irrigation.

Entities:

```text
IrrigationZone
IrrigationHead
DripZone
Valve
Controller
```

Important attributes:

```text
planting type
precipitation method
water demand
coverage
status
```

Initial version does not need hydraulic pipe-sizing calculations.

---

# 23. Lighting

Represent exterior landscape lighting.

Entities:

```text
path_light
uplight
downlight
step_light
wall_light
tree_light
accent_light
```

Required data:

```text
location
fixture_type
target
circuit
existing/proposed
phase
```

---

# 24. Existing Conditions Model

Existing site data should live separately from proposed designs.

Recommended:

```text
existing_conditions.yaml
```

This file represents the site before the landscape project begins.

Concepts should never overwrite existing conditions.

---

# 25. Site Analysis

The analysis system should support analytical overlays.

Examples:

```text
sun
shade
drainage
privacy
views
noise
circulation
heat
wind
activity
maintenance
problem areas
opportunity areas
```

Overlays should be stored or calculated separately from physical site entities.

---

# 26. Analysis Zones

Generic analysis entity:

```python
AnalysisZone
```

Fields:

```text
geometry
analysis_type
severity
description
confidence
source
```

Example:

```yaml
- id: SHADE001
  analysis_type: afternoon_shade
  severity: high
  geometry:
    ...
```

---

# 27. Sun and Shade

Phase 1 may use manually defined shade regions.

Example:

```yaml
light_zones:
  - id: LIGHT001
    category: full_sun
    geometry: ...
```

Suggested categories:

```text
full_sun
morning_sun
afternoon_sun
part_sun
part_shade
deep_shade
reflected_heat
```

Later versions may calculate solar exposure using:

```text
latitude
longitude
date
time
structure heights
tree canopy
tree height
```

Do not block the first release on advanced solar simulation.

---

# 28. Views

Represent visual relationships explicitly.

Model:

```python
ViewCorridor
```

Types:

```text
desirable
undesirable
privacy_issue
focal_view
screening_target
```

Example:

```yaml
- id: VIEW001
  type: undesirable
  origin: rear_patio
  target: neighbor_hvac
  priority: high
```

---

# 29. Circulation

Represent current and proposed movement patterns.

Model:

```python
CirculationPath
```

Types:

```text
primary
secondary
service
informal
undesired
```

Fields:

```text
geometry
width
surface
frequency
accessible
```

---

# 30. Activity Zones

Represent functional use of outdoor areas.

Examples:

```text
children_play
dog
dining
grilling
entertaining
gardening
storage
pool
sports
quiet
service
```

Entity:

```python
ActivityZone
```

---

# 31. Outdoor Rooms

Outdoor rooms are a major design concept and should be first-class objects.

Entity:

```python
OutdoorRoom
```

Suggested fields:

```text
name
geometry
uses
capacity
shade_requirement
privacy_requirement
weather_protection
adjacency_requirements
view_preferences
utility_requirements
```

Example:

```yaml
- id: ROOM001
  name: Main Outdoor Dining

  uses:
    - dining
    - entertaining

  desired_capacity: 10

  requirements:
    shade: 0.80
    privacy: 0.60

  adjacency:
    prefer:
      - kitchen_exit

  avoid_views:
    - neighbor_hvac
```

---

# 32. User Program

Create:

```text
program.yaml
```

The program describes what the homeowner wants the property to accomplish.

Example:

```yaml
goals:

  outdoor_dining:
    priority: 10

  shade:
    priority: 10

  privacy:
    priority: 9

  low_maintenance:
    priority: 8

  entertaining:
    priority: 8

  lawn:
    priority: 5
```

Also capture:

```text
budget preference
maintenance tolerance
water-use preference
construction tolerance
DIY preference
expected years in home
entertaining size
children
pets
storage
desired architectural style
```

---

# 33. Concept Plans

The system must support multiple concepts.

Examples:

```text
Concept A — Texas Modern / Low Maintenance
Concept B — Outdoor Living
Concept C — Garden / Resort
```

Concepts should be genuinely different spatial strategies.

They should not merely differ by plant palette.

---

# 34. Concept Data Model

Each concept should inherit from existing conditions.

Do not duplicate the entire property file.

Represent concept changes explicitly.

Example:

```yaml
concept:
  id: concept_a
  name: Texas Modern

operations:

  - operation: remove
    entity_id: BED004

  - operation: update
    entity_id: LAWN001
    geometry:
      ...

  - operation: add
    entity:
      id: PATIO_NEW_001
      type: hardscape
      subtype: patio
      geometry:
        ...
```

Supported concept operations:

```text
add
update
remove
preserve
```

This produces an auditable design diff.

---

# 35. Concept Evaluation

Concepts should support deterministic scoring.

Example criteria:

```yaml
criteria:

  outdoor_usage:
    weight: 0.25

  maintenance:
    weight: 0.15

  cost:
    weight: 0.15

  shade:
    weight: 0.10

  privacy:
    weight: 0.10

  water_usage:
    weight: 0.10

  aesthetics:
    weight: 0.10

  phasing:
    weight: 0.05
```

Weights should normally total:

```text
1.0
```

Scores may initially be manually assigned on a scale such as:

```text
0–10
```

Calculated total:

```text
total_score =
Σ(score × weight)
```

The software should display the raw assumptions.

Never present a weighted score as objective truth when the underlying score was human-assigned.

---

# 36. Hard Constraints vs Soft Objectives

The system must distinguish:

## Hard constraints

A plan is invalid if violated.

Examples:

```text
structure outside parcel
blocked required utility access
invalid polygon
proposed tree located inside house
hardscape crossing forbidden easement
```

## Soft objectives

A plan remains valid but may score poorly.

Examples:

```text
insufficient shade
high maintenance
high cost
poor privacy
excess lawn
long circulation route
```

---

# 37. Master Plan

The selected design should become:

```text
master_plan.yaml
```

The master plan may be:

- one chosen concept,
- a modified concept,
- a hybrid of multiple concepts.

The master plan should not modify the original concept files.

---

# 38. Multi-Year Phasing

The system should support implementation over multiple years.

Entity:

```python
ProjectPhase
```

Fields:

```text
id
name
year
sequence
scope
dependencies
budget
entities_added
entities_removed
```

Example:

```yaml
phases:

  - id: PHASE0
    name: Investigation and Cleanup
    year: 2026

  - id: PHASE1
    name: Landscape Skeleton
    year: 2027

  - id: PHASE2
    name: Outdoor Living
    year: 2028

  - id: PHASE3
    name: Planting Refinement
    year: 2029
```

---

# 39. Phase Dependency Validation

The software should identify sequencing conflicts.

Example:

```text
Phase 1 installs planting bed.
Phase 2 removes planting bed to build patio.
```

This should produce a warning.

Example:

```text
REWORK WARNING:
BED021 is installed during Phase 1 and demolished during Phase 2.
Estimated avoidable cost: $2,300.
```

One major purpose of the system is minimizing future rework.

---

# 40. Cost Model

Costs should remain transparent and editable.

Use:

```text
costs.yaml
```

Example:

```yaml
unit_costs:

  mulch:
    unit: cubic_yard
    low: 45
    expected: 65
    high: 90

  concrete_patio:
    unit: sqft
    low: 12
    expected: 18
    high: 28

  five_gallon_shrub:
    unit: each
    low: 35
    expected: 55
    high: 90
```

Do not hard-code current market prices into application code.

---

# 41. Cost Calculations

Costs should derive quantities from geometry when possible.

Example:

```text
mulch bed area
        ↓
mulch depth
        ↓
cubic yards
        ↓
unit cost
        ↓
estimated cost
```

Provide:

```text
low
expected
high
```

rather than false precision.

Support:

```text
contingency
tax
design fees
permit allowance
contractor overhead
inflation
```

---

# 42. Quantity Calculations

Automatically calculate where possible:

```text
lawn square footage
planting bed square footage
hardscape square footage
fence linear footage
edging linear footage
mulch cubic yards
gravel cubic yards
plant counts
tree counts
lighting fixture counts
irrigation zone counts
```

---

# 43. Plant Database

Create a structured plant catalog.

Plant selection should occur after concept geometry.

Suggested model:

```python
PlantSpecies
```

Fields:

```text
botanical_name
common_name
plant_type
native_status
evergreen
mature_height
mature_width
minimum_spacing
sun
water
soil
flower_color
bloom_period
wildlife_value
maintenance
heat_tolerance
cold_tolerance
notes
```

Example:

```yaml
- botanical_name: Ilex vomitoria
  common_name: Yaupon Holly

  type: shrub

  native_status: native

  mature:
    height_ft: 12
    width_ft: 8

  sun:
    - full_sun
    - part_shade

  water: low
```

Do not initially attempt to create a massive national plant database.

Build plants required by the reference project first.

---

# 44. Planting Design

Individual plants may be modeled as:

```python
PlantInstance
```

Mass plantings should also be supported.

```python
PlantMass
```

A planting mass is preferable where the design uses repeated species.

Example:

```yaml
- id: MASS001

  species: Muhlenbergia capillaris

  geometry:
    ...

  spacing_ft: 3

  layout: staggered
```

The software can calculate approximate required quantity.

---

# 45. Mature Plant Geometry

Planting should support current and mature dimensions.

Example:

```text
installation size
year 3 size
year 5 size
mature size
```

Future capability:

```python
tree.canopy_radius(year=10)
```

This can support visualization of how the landscape changes over time.

---

# 46. Validation Engine

Implement a dedicated validation system.

Output categories:

```text
ERROR
WARNING
INFO
```

Examples:

```text
ERROR:
Parcel polygon is invalid.

ERROR:
TREE017 is located inside STRUCT001.

WARNING:
Planting BED006 overlaps utility service clearance.

WARNING:
Proposed tree canopy may conflict with roof at maturity.

WARNING:
Outdoor dining area has low modeled afternoon shade.

INFO:
Total proposed lawn decreased by 1,850 sqft.
```

---

# 47. Initial Validation Rules

Implement at minimum:

1. All polygons must be valid.
2. Entity IDs must be unique.
3. Required references must exist.
4. Proposed geometry should remain within the parcel unless explicitly permitted.
5. Trees cannot be centered within buildings.
6. Conflicting hardscape geometries should be flagged.
7. Utility clearance conflicts should be flagged.
8. Removed entities must exist.
9. Concept update operations must reference existing entities.
10. Phase dependencies must reference valid phases.

---

# 48. Drawing System

The system should produce professional vector drawings.

Primary format:

```text
SVG
```

Secondary:

```text
PDF
DXF
```

SVG should be the first rendering target because it is:

- deterministic,
- inspectable,
- scalable,
- web-compatible,
- easy to test,
- easy to convert.

---

# 49. Drawing Sheets

Initial supported sheet sizes:

```text
11 × 17 inches
24 × 36 inches
```

Landscape orientation should be supported.

Drawing metadata:

```text
sheet number
sheet title
project name
date
revision
scale
north arrow
legend
notes
```

---

# 50. Proposed Drawing Set

Eventually support:

```text
L0.0  Cover / Project Overview

L1.0  Existing Conditions

L1.1  Site Analysis

L2.0  Concept A
L2.1  Concept B
L2.2  Concept C

L3.0  Master Landscape Plan

L3.1  Dimension Plan

L4.0  Hardscape Plan

L5.0  Planting Plan

L5.1  Plant Schedule

L6.0  Irrigation Concept

L7.0  Lighting Plan

L8.0  Drainage Concept

L9.0  Phasing Plan

L10.0 Cost Plan
```

Do not implement all sheets in Milestone 1.

---

# 51. Drawing Scale

Support real architectural scales.

Examples:

```text
1" = 10'
1" = 20'
1/8" = 1'
1/4" = 1'
```

The geometry model always remains in real-world units.

The renderer applies scaling.

---

# 52. Drawing Styles

Styles should be semantic.

Bad:

```python
stroke_width = 3
```

distributed throughout drawing code.

Good:

```python
style.existing_structure
style.proposed_structure
style.property_line
style.existing_tree
style.proposed_tree
style.dimension
```

Keep presentation rules centralized.

Do not encode semantic meaning exclusively through color.

Drawings should remain understandable when printed in grayscale.

---

# 53. Layering

Recommended rendering layers:

```text
00_background
10_property
20_existing_structures
30_existing_hardscape
40_existing_vegetation
50_analysis
60_proposed_hardscape
70_proposed_vegetation
80_annotations
90_dimensions
95_legend
99_titleblock
```

DXF exports should use equivalent named layers where practical.

---

# 54. Symbols

Create reusable vector symbols for:

```text
existing tree
proposed tree
shrub
plant mass
light
irrigation head
drain
utility
north arrow
spot elevation
```

Symbols must scale consistently.

---

# 55. Dimensions

Implement dimension objects independently from plain text.

Examples:

```text
linear dimension
aligned dimension
radius
area label
coordinate callout
```

Dimension values should derive from geometry.

Never manually type a dimensional value that can be calculated.

---

# 56. Annotations

Annotations should support:

```text
leaders
labels
notes
keynotes
callouts
```

Each annotation should be associated with an entity where possible.

---

# 57. PDF Output

PDF should be generated from deterministic vector content.

Preferred workflow:

```text
project
   ↓
SVG
   ↓
PDF
```

Avoid rasterizing the site plan.

---

# 58. DXF Output

DXF is a secondary professional interoperability format.

Use:

```text
ezdxf
```

DXF should contain meaningful layers and geometry.

Initial DXF support may be limited to:

```text
parcel
structures
hardscape
trees
beds
annotations
```

---

# 59. CLI

Create a clean command-line interface first.

Example:

```bash
landscape validate projects/greenleaf
```

```bash
landscape render projects/greenleaf --sheet existing
```

```bash
landscape render projects/greenleaf --concept concept_a
```

```bash
landscape estimate projects/greenleaf --concept concept_a
```

```bash
landscape compare projects/greenleaf
```

Potential commands:

```text
validate
render
estimate
compare
report
export-dxf
list-entities
inspect
```

---

# 60. No GUI Initially

Do not build a graphical editor during early milestones.

First prove:

```text
structured data
+
geometry
+
analysis
+
rendering
```

Once the project format is stable, a graphical interface can be added.

A future UI may provide:

- drag/drop geometry
- survey tracing
- property visualization
- layers
- concept switching
- measurement tools
- plant placement

But the GUI must remain a client of the underlying deterministic model.

---

# 61. Project Versioning

The project schema needs an explicit version.

Example:

```yaml
schema_version: 1
```

Create migration mechanisms when breaking schema changes occur.

Never silently reinterpret old project files.

---

# 62. Reproducibility Metadata

Generated reports should include:

```text
project revision
schema version
software version
generation timestamp
concept ID
master-plan version
```

Optional:

```text
git commit hash
```

---

# 63. Photo Survey

Support a structured photographic survey.

Model:

```python
SitePhoto
```

Fields:

```text
filename
camera_location
direction_degrees
description
date
tags
```

Example:

```yaml
- id: PHOTO001
  filename: backyard_northwest.jpg
  camera_location: [42, 80]
  direction_degrees: 315
  tags:
    - backyard
    - privacy
```

Future drawings may show photo-location arrows.

---

# 64. Reference Documents

The project should track source documents.

Examples:

```text
property survey
HOA rules
plat
contractor proposal
utility drawing
irrigation drawing
soil test
plant nursery estimate
```

Represent references in metadata.

Do not require the system to parse them initially.

---

# 65. AI Integration Philosophy

AI integration is optional and layered on top of the deterministic model.

AI may:

- interpret homeowner goals,
- suggest design concepts,
- explain tradeoffs,
- suggest plants,
- identify likely issues,
- propose structured modifications,
- summarize plan differences,
- produce narratives.

AI must not directly edit drawing files.

Instead:

```text
AI suggestion
     ↓
structured proposed operation
     ↓
schema validation
     ↓
geometry validation
     ↓
human review
     ↓
project modification
```

Example AI-generated proposal:

```yaml
operation: add

entity:
  id: TREE_NEW_004
  type: tree
  species: Quercus shumardii
  location: [44.2, 88.1]

reason:
  Increase afternoon shade over proposed patio.
```

---

# 66. AI Guardrail

Never allow this workflow:

```text
prompt
  ↓
AI drawing
  ↓
authoritative geometry
```

AI perspective renderings may be used only for visualization.

They are not construction geometry.

---

# 67. Design Alternatives

Concept alternatives should be evaluated across consistent dimensions.

Possible dimensions:

```text
initial cost
long-term cost
maintenance
water demand
shade
privacy
outdoor usability
construction complexity
implementation risk
amount of demolition
future flexibility
plant diversity
lawn area
hardscape area
```

The comparison report should show raw quantities whenever possible.

Example:

```text
Concept A lawn: 3,200 sqft
Concept B lawn: 2,100 sqft
Concept C lawn: 1,350 sqft
```

This is more informative than only displaying subjective scores.

---

# 68. Scenario Comparison Report

Generate a comparison such as:

| Metric | Concept A | Concept B | Concept C |
|---|---:|---:|---:|
| Lawn sqft | 3,200 | 2,100 | 1,350 |
| New hardscape sqft | 450 | 1,200 | 800 |
| New trees | 5 | 7 | 11 |
| Estimated cost | $ | $$ | $$$ |
| Maintenance | Low | Medium | High |
| Weighted score | 8.2 | 8.8 | 7.9 |

The underlying report should include exact calculated values.

---

# 69. Professional Quality Standard

Generated plans should look intentional and professional.

Avoid:

- arbitrary font sizes,
- overlapping labels,
- inconsistent symbols,
- excessive decorative elements,
- fake precision,
- unscaled geometry,
- undocumented assumptions.

Prioritize:

- hierarchy,
- legibility,
- alignment,
- scale,
- white space,
- consistent line weights,
- semantic symbols,
- clear legends.

---

# 70. Testing Strategy

Use:

```text
pytest
```

Tests should include:

```text
unit tests
integration tests
schema tests
geometry tests
render tests
golden-file tests
```

---

# 71. Geometry Tests

Test:

```text
area
length
centroid
intersection
containment
buffer
distance
validity
```

Example:

```python
def test_rectangular_lawn_area():
    lawn = polygon([(0,0), (10,0), (10,20), (0,20)])
    assert lawn.area == 200
```

---

# 72. Model Tests

Test:

```text
unique IDs
valid references
YAML parsing
serialization roundtrip
schema versions
concept operations
```

This should work:

```text
YAML
 ↓
model
 ↓
YAML
```

without material information loss.

---

# 73. Golden Drawing Tests

Create a few deterministic fixture properties.

Render SVG.

Canonicalize SVG where necessary.

Compare output against approved reference drawings.

Do not overuse fragile pixel-based screenshot tests.

Prefer structural SVG comparisons.

---

# 74. Reference Test Property

Before the real property survey is entered, create a synthetic test property.

Example:

```text
80 ft × 130 ft parcel
rectangular house
driveway
patio
three trees
two planting beds
fence
```

This will allow development of the rendering engine before actual field data is complete.

---

# 75. Logging

Use structured and useful logs.

Example:

```text
Loaded project greenleaf.
Validated 47 entities.
Found 2 warnings.
Generated L1.0 Existing Conditions.
Output: generated/svg/L1.0.svg
```

Do not flood output with low-level geometry internals by default.

---

# 76. Error Handling

Errors should explain:

```text
what failed
where
why
how to correct it
```

Bad:

```text
Invalid geometry.
```

Better:

```text
BED004 contains a self-intersecting polygon near coordinate (31.2, 48.9).
Correct the polygon before rendering.
```

---

# 77. Architecture Decision Records

When significant implementation decisions are made that are not resolved by this specification, create lightweight ADR files.

Example:

```text
docs/adr/0001-svg-renderer.md
```

An ADR should describe:

```text
decision
context
alternatives considered
reason
consequences
```

This prevents implementation assumptions from becoming invisible.

---

# 78. Initial Development Milestones

Development should be incremental.

Do not attempt the entire specification at once.

---

# 79. Milestone 0 — Repository Foundation

Deliver:

```text
Python project
uv configuration
package structure
pytest
basic CLI
schema versioning
README
```

CLI:

```bash
landscape --help
```

must work.

Acceptance criteria:

```text
uv sync succeeds
pytest succeeds
CLI starts successfully
```

---

# 80. Milestone 1 — Existing Conditions Geometry

This is the first meaningful release.

Support:

```text
parcel
structures
hardscape
trees
planting beds
lawn
fences
utilities
```

Input:

```text
YAML
```

Output:

```text
SVG existing-conditions plan
```

Required drawing elements:

```text
parcel boundary
house
driveway
patios
fences
trees
beds
lawn
labels
north arrow
graphic scale
title block
```

Acceptance criteria:

```bash
landscape validate projects/greenleaf
```

works.

And:

```bash
landscape render projects/greenleaf --sheet existing
```

produces:

```text
generated/svg/L1.0_existing_conditions.svg
```

---

# 81. Milestone 1 Priority

Do not start advanced analysis until Milestone 1 produces a convincing plan.

The user should be able to inspect the drawing and say:

> Yes, this accurately represents my property.

Accuracy of the base plan is more important than feature count.

---

# 82. Milestone 2 — Site Analysis

Add:

```text
sun/shade zones
views
privacy
circulation
drainage paths
activity zones
problem areas
opportunity areas
```

Output:

```text
L1.1 Site Analysis
```

---

# 83. Milestone 3 — Concepts

Support:

```text
Concept A
Concept B
Concept C
```

using explicit concept operations.

Add:

```text
concept rendering
concept metrics
concept comparison
weighted scoring
```

Output:

```text
L2.0
L2.1
L2.2
concept comparison report
```

---

# 84. Milestone 4 — Master Plan

Support creation of:

```text
master_plan.yaml
```

Output:

```text
L3.0 Master Landscape Plan
```

Include:

```text
proposed outdoor rooms
hardscape
trees
beds
lawn
major planting masses
```

---

# 85. Milestone 5 — Cost and Phasing

Add:

```text
quantity engine
unit costs
low/base/high estimates
project phases
dependency validation
rework warnings
```

Output:

```text
cost report
phase report
L9.0 Phasing Plan
L10.0 Cost Plan
```

---

# 86. Milestone 6 — Detailed Planting

Add:

```text
plant database
plant instances
plant masses
spacing
plant quantities
mature dimensions
plant schedule
```

Output:

```text
L5.0 Planting Plan
L5.1 Plant Schedule
```

---

# 87. Milestone 7 — Infrastructure Concepts

Add:

```text
irrigation concept
lighting
drainage concept
```

These should remain conceptual unless appropriate engineering has been performed.

---

# 88. Milestone 8 — Professional Export

Add:

```text
PDF drawing set
DXF
CSV quantities
project report
```

Produce a cohesive drawing package.

---

# 89. Future Milestone — Interactive Editor

Only after the model is stable consider:

```text
browser interface
interactive map
drag/drop geometry
measurement tools
photo placement
layer controls
concept switching
```

Possible architecture:

```text
Python core
    ↓
FastAPI
    ↓
web client
```

The Python domain model remains authoritative.

---

# 90. Future Milestone — Survey Tracing

Potential workflow:

```text
import survey PDF/image
        ↓
select two known points
        ↓
calibrate scale
        ↓
rotate north
        ↓
trace geometry
        ↓
store real-world coordinates
```

This could dramatically improve data entry but is not required for initial development.

---

# 91. Future Milestone — Aerial Calibration

Potential workflow:

```text
aerial image
   ↓
known property dimensions
   ↓
geometric calibration
   ↓
background reference layer
```

Aerial imagery must never override surveyed boundaries.

---

# 92. Future Milestone — Solar Modeling

Potential future model:

```text
property latitude
date
time
solar azimuth
solar elevation
structure height
tree height
tree canopy
```

Generate shade polygons for representative periods:

```text
summer morning
summer afternoon
winter morning
winter afternoon
```

This should be implemented only after accurate elevations and heights are available.

---

# 93. Future Milestone — Growth Simulation

Support visualizing:

```text
installation
year 3
year 5
year 10
maturity
```

This is especially valuable for trees and privacy screening.

---

# 94. Future Milestone — Optimization

Do not begin with automatic landscape optimization.

Eventually the system may suggest candidate configurations using constraints.

Examples:

```text
maximize patio shade
minimize irrigation
maximize privacy
minimize installation cost
minimize future demolition
```

Optimization results should be recommendations, not authoritative designs.

---

# 95. Implementation Rules for Coding Agents

Any coding agent implementing this project must follow these rules.

## Rule 1

Read this specification before modifying architecture.

## Rule 2

Implement the current milestone only unless prerequisite work requires otherwise.

Do not jump ahead and build speculative features.

## Rule 3

Prefer simple, explicit, testable architecture.

Do not create abstractions solely because they may theoretically be useful later.

## Rule 4

Use the Greenleaf reference project to drive real requirements.

Avoid creating generic capabilities without a concrete use case.

## Rule 5

All authoritative geometry must be structured data.

Never make generated SVG or PDF authoritative.

## Rule 6

All calculations must be deterministic.

## Rule 7

Keep rendering logic separate from domain logic.

## Rule 8

Do not use an LLM to perform numerical geometry calculations.

## Rule 9

Use strong schema validation.

## Rule 10

Write tests for every important geometry or project-data feature.

## Rule 11

Do not silently fix invalid input unless the correction is mathematically unambiguous.

Prefer a validation message.

## Rule 12

When making an architectural decision not covered here, document it in an ADR.

## Rule 13

Do not add a database server until project-file storage is demonstrably insufficient.

## Rule 14

Do not build a GUI until CLI and source-file workflows are stable.

## Rule 15

At the end of each implementation task:

1. Run tests.
2. Run relevant validation commands.
3. Generate representative output.
4. Summarize files changed.
5. State remaining limitations.
6. Identify the next smallest useful step.

---

# 96. Coding Standards

Prefer:

```text
typed Python
small modules
explicit models
pure calculations where possible
dependency injection where useful
clear naming
minimal global state
```

Use type hints.

Use docstrings for public APIs.

Avoid deeply clever implementations.

Landscape geometry should be understandable to another developer reading the code.

---

# 97. Deterministic Output Rules

Generated files should be stable across runs.

Avoid random:

```text
IDs
ordering
timestamps inside geometry
floating-point formatting
SVG element ordering
```

Sort entities by stable identifiers where appropriate.

Use consistent coordinate precision.

Recommended initial geometry precision:

```text
0.001 ft internally where practical
```

Display precision should depend on the drawing.

Do not imply field accuracy beyond the source measurements.

---

# 98. Security and Privacy

Residential projects may contain sensitive property information.

The application should:

- operate locally by default,
- avoid uploading source documents automatically,
- avoid embedding unnecessary personal data into drawings,
- allow title blocks to omit street address,
- distinguish public project metadata from private project metadata.

---

# 99. Initial Greenleaf Workflow

The initial real-world workflow should be:

```text
Step 1
Obtain closing/property survey.

Step 2
Create calibrated property boundary.

Step 3
Trace/model house footprint.

Step 4
Add driveway and sidewalks.

Step 5
Add patios and major hardscape.

Step 6
Add fences and gates.

Step 7
Add trees.

Step 8
Add existing beds and lawn.

Step 9
Add utility equipment.

Step 10
Validate dimensions against field measurements.

Step 11
Generate L1.0 Existing Conditions.

Step 12
Perform structured photo survey.

Step 13
Add site-analysis information.

Step 14
Generate L1.1 Site Analysis.

Step 15
Create homeowner program.

Step 16
Develop three concept alternatives.

Step 17
Compare concepts.

Step 18
Create master plan.

Step 19
Create multi-year implementation strategy.

Step 20
Develop technical planting and infrastructure plans.
```

---

# 100. Immediate First Implementation Task

The coding agent should begin with:

```text
Milestone 0 + the minimum required portion of Milestone 1.
```

Implement:

```text
1. Python project using uv
2. LandscapeProject model
3. Coordinate system model
4. Parcel model
5. Structure model
6. HardscapeArea model
7. Tree model
8. PlantingBed model
9. LawnArea model
10. YAML loading
11. Project validation
12. Basic SVG renderer
13. North arrow
14. Graphic scale
15. Basic title block
16. CLI validate command
17. CLI render command
18. Unit tests
19. One synthetic fixture project
20. Initial Greenleaf project folder
```

Do not implement:

```text
plant database
cost estimating
solar calculation
GUI
AI integration
automatic concept generation
advanced drainage
DXF
```

during this first implementation task.

---

# 101. First Demonstration

The first demonstration should render a synthetic residential site resembling:

```text
80 × 130 ft parcel

house:
approximately 55 × 45 ft

driveway

rear patio

fence

3 existing trees

2 planting beds

lawn
```

Output:

```text
examples/generated/L1.0_existing_conditions.svg
```

The drawing should visibly demonstrate:

```text
correct scale
professional line hierarchy
tree symbols
structure footprint
hardscape
planting areas
labels
north arrow
graphic scale
title block
```

---

# 102. Milestone 1 Definition of Done

Milestone 1 is complete when:

1. A real property can be represented in YAML.
2. Geometry is validated.
3. Quantities such as area and length are calculated correctly.
4. The project can be rendered to an accurate vector site plan.
5. The plan is drawn to scale.
6. The drawing is visually professional enough to review design decisions.
7. The entire output can be reproduced from source files.
8. Unit and integration tests pass.
9. No graphical editor is required.
10. The real Greenleaf project can begin replacing synthetic geometry with surveyed geometry.

---

# 103. First Command Sequence

The desired developer experience should eventually resemble:

```bash
git clone <repository>

cd landscape-planner

uv sync

uv run pytest

uv run landscape validate projects/greenleaf

uv run landscape render projects/greenleaf --sheet existing
```

Expected result:

```text
Validation successful.

Entities:
  Parcel: 1
  Structures: 1
  Hardscape: 3
  Trees: 7
  Planting beds: 5
  Lawn areas: 2

Warnings: 2

Generated:
projects/greenleaf/generated/svg/L1.0_existing_conditions.svg
```

---

# 104. Long-Term Success Criteria

The project is successful if the homeowner can eventually answer questions such as:

```text
What should my finished yard look like?

What are three materially different ways to solve the property?

Which concept best meets our priorities?

How much lawn exists in each option?

Which option gives us the most shade?

Which option requires the least maintenance?

Where should new trees be installed?

What should be built first?

What should we avoid installing now because later construction would destroy it?

How much should each phase approximately cost?

What plants are required?

How many cubic yards of mulch are needed?

What would the yard look like in five or ten years?

Can a landscape contractor understand the plan?

Can a landscape architect or designer easily review and modify it?
```

The system should make these answers traceable to project data rather than intuition alone.

---

# 105. Guiding Principle

The most important principle of the project is:

> **Do not optimize for generating a beautiful picture. Optimize for creating a correct, inspectable, editable, phased landscape design that can eventually produce beautiful real-world outdoor spaces.**

The final plan should be a consequence of sound geometry, analysis, priorities, and design decisions.

The software exists to make those decisions clearer, more reproducible, and easier to execute over multiple years.
