"""Concept resolution preserves its inputs and reconciles with core quantities."""

import json

import pytest

from landscape_planner.model.project import LandscapeProject
from landscape_planner.planning.concepts import (
    Concept, ConceptOperation, apply_operations, compare_projects, resolve_concept,
)


def polygon(x=1, y=1, size=2):
    return {"type": "polygon", "coordinates": [
        [x, y], [x + size, y], [x + size, y + size], [x, y + size],
    ]}


@pytest.fixture
def baseline():
    return LandscapeProject.model_validate({
        "project": {"id": "site", "name": "Test site"},
        "existing_conditions": {
            "parcel": {"id": "parcel", "boundary": polygon(0, 0, 100)},
            "hardscape": [{"id": "patio", "subtype": "patio", "geometry": polygon()}],
            "trees": [{"id": "oak", "location": [30, 30], "canopy_radius_ft": 4}],
            "utilities": [{"id": "meter", "type": "water", "location": [50, 50]}],
        },
    })


def op(action, entity_id="patio", category="hardscape", **data):
    return ConceptOperation(action=action, category=category, entity_id=entity_id, data=data)


def test_resolver_deep_copies_baseline_and_operations(baseline):
    concept = Concept(id="a", name="Alternative", operations=[
        op("update", geometry=polygon(size=4), notes=["Expanded"]),
        op("add", "bed", "planting_beds", geometry=polygon(10, 10)),
        op("remove", "oak", "trees"),
        op("preserve", "meter", "utilities"),
    ])
    before, authored = baseline.model_dump(), concept.model_dump()
    resolved = resolve_concept(baseline, concept)
    assert resolved.existing_conditions.hardscape[0].area_sqft == 16
    assert resolved.coordinate_system == baseline.coordinate_system
    assert resolved.existing_conditions.parcel == baseline.existing_conditions.parcel
    resolved.existing_conditions.parcel.notes.append("Independent")
    resolved.existing_conditions.hardscape[0].notes.append("Later")
    assert baseline.model_dump() == before
    assert concept.model_dump() == authored


def test_comparison_quantities_reconcile_and_are_json_safe(baseline):
    after = apply_operations(baseline, [
        op("update", geometry=polygon(size=4)),
        op("add", "bed", "planting_beds", geometry=polygon(10, 10)),
        op("remove", "oak", "trees"),
    ])
    comparison = compare_projects(baseline, after)
    assert comparison["added"] == ["bed"]
    assert comparison["removed"] == ["oak"]
    assert comparison["modified"] == ["patio"]
    assert comparison["preserved"] == ["meter"]
    quantities = {row["category"]: row for row in comparison["quantity_deltas"]}
    assert quantities["hardscape"] == {
        "category": "hardscape", "unit": "sqft", "before": 4, "after": 16, "delta": 12,
    }
    assert quantities["planting_bed"]["delta"] == 4
    assert quantities["tree"]["delta"] == -1
    assert quantities["parcel"]["delta"] == 0
    assert json.loads(json.dumps(comparison, allow_nan=False)) == comparison


@pytest.mark.parametrize("operation, message", [
    (op("update", "missing", name="No"), "Unknown entity"),
    (op("remove", "oak"), "Unknown entity"),
    (op("add", "oak", geometry=polygon(), subtype="patio"), "duplicate"),
    (op("add", "parcel", geometry=polygon(), subtype="patio"), "duplicate"),
    (op("update", geometry=polygon(101, 101)), "GEOMETRY_OUTSIDE_PARCEL"),
    (op("update", geometry={"type": "point", "coordinates": [1, 1]}), "EXPECTED_POLYGON"),
    (op("update", source={"reference": "undeclared"}), "UNKNOWN_SOURCE_REFERENCE"),
    (op("update", unsupported_field=True), "Extra inputs"),
])
def test_invalid_operations_are_atomic(baseline, operation, message):
    before = baseline.model_dump()
    with pytest.raises(ValueError, match=message):
        apply_operations(baseline, [op("update", notes=["Earlier operation"]), operation])
    assert baseline.model_dump() == before


@pytest.mark.parametrize("action", ["update", "remove"])
def test_preserve_blocks_subsequent_mutation(baseline, action):
    change = op(action, **({"name": "New name"} if action == "update" else {}))
    with pytest.raises(ValueError, match="preserved"):
        apply_operations(baseline, [op("preserve"), change])


@pytest.mark.parametrize("data", [
    {"action": "add", "category": "parcel", "entity_id": "p"},
    {"action": "rename", "category": "trees", "entity_id": "oak"},
    {"action": "remove", "category": "trees", "entity_id": "oak", "data": {"name": "x"}},
    {"action": "update", "category": "trees", "entity_id": "oak", "data": {"id": "new"}},
    {"action": "update", "category": "trees", "entity_id": "oak"},
    {"action": "preserve", "category": "trees", "entity_id": " "},
])
def test_operation_schema_rejects_invalid_contract(data):
    with pytest.raises(ValueError):
        ConceptOperation.model_validate(data)


def test_utility_yaml_alias_can_be_updated(baseline):
    after = apply_operations(baseline, [op("update", "meter", "utilities", type="gas")])
    assert after.existing_conditions.utilities[0].utility_type == "gas"


def test_self_intersecting_geometry_rejected(baseline):
    with pytest.raises(ValueError, match="INVALID_POLYGON"):
        apply_operations(baseline, [op("update", geometry={
            "type": "polygon", "coordinates": [[1, 1], [5, 5], [1, 5], [5, 1]],
        })])


def test_empty_concept_is_independent_and_validates_baseline(baseline):
    resolved = resolve_concept(baseline, Concept(id="none", name="Keep existing"))
    assert resolved == baseline
    assert resolved is not baseline
    assert resolved.existing_conditions.trees[0] is not baseline.existing_conditions.trees[0]
    baseline.existing_conditions.trees[0].location = (150, 150)
    with pytest.raises(ValueError, match="TREE_OUTSIDE_PARCEL"):
        apply_operations(baseline, [])
