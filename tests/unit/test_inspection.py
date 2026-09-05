from pathlib import Path

from landscape_planner.inspection import (
    calculated_metrics,
    entity_display_name,
    entity_inspection_payload,
    entity_to_dict,
    find_entity,
    iter_inspectable_entities,
)
from landscape_planner.io.yaml_loader import load_project


FIXTURE = Path("tests/fixtures/synthetic")


def test_find_entity_returns_category_and_entity():
    project = load_project(FIXTURE)

    result = find_entity(project, "TREE001")

    assert result is not None
    assert result.category == "tree"
    assert result.entity.id == "TREE001"


def test_iter_inspectable_entities_has_deterministic_order():
    project = load_project(FIXTURE)

    entity_ids = [item.entity.id for item in iter_inspectable_entities(project)]

    assert entity_ids[:5] == [
        "REF_SURVEY_SYNTHETIC",
        "PHOTO_BACKYARD_001",
        "PARCEL001",
        "HOUSE001",
        "DOOR_REAR001",
    ]
    assert entity_ids[-1] == "UTIL001"


def test_entity_display_name_uses_domain_specific_fallbacks():
    project = load_project(FIXTURE)

    tree = find_entity(project, "TREE001")
    utility = find_entity(project, "UTIL001")

    assert entity_display_name(tree) == "Live Oak"
    assert entity_display_name(utility) == "HVAC Condenser"


def test_find_entity_supports_nested_doors():
    project = load_project(FIXTURE)

    result = find_entity(project, "DOOR_REAR001")

    assert result is not None
    assert result.category == "door"
    assert result.entity.id == "DOOR_REAR001"


def test_find_entity_returns_none_for_missing_id():
    project = load_project(FIXTURE)

    assert find_entity(project, "MISSING") is None


def test_entity_to_dict_uses_yaml_aliases():
    project = load_project(FIXTURE)
    result = find_entity(project, "UTIL001")

    data = entity_to_dict(result.entity)

    assert data["id"] == "UTIL001"
    assert data["type"] == "hvac"
    assert "utility_type" not in data


def test_calculated_metrics_include_polygon_area_centroid_and_bounds():
    project = load_project(FIXTURE)
    result = find_entity(project, "PARCEL001")

    metrics = calculated_metrics(result.entity)

    assert metrics["geometry_type"] == "Polygon"
    assert metrics["bounds"] == [0.0, 0.0, 80.0, 130.0]
    assert metrics["centroid"] == [40.0, 65.0]
    assert metrics["area_sqft"] == 10400.0
    assert metrics["perimeter_ft"] == 420.0


def test_calculated_metrics_include_tree_canopy_area():
    project = load_project(FIXTURE)
    result = find_entity(project, "TREE001")

    metrics = calculated_metrics(result.entity)

    assert metrics["geometry_type"] == "Point"
    assert metrics["canopy_radius_ft"] == 13.0
    assert metrics["canopy_area_sqft"] == 530.077


def test_calculated_metrics_include_utility_clearance_area():
    project = load_project(FIXTURE)
    result = find_entity(project, "UTIL001")

    metrics = calculated_metrics(result.entity)

    assert metrics["geometry_type"] == "Point"
    assert metrics["clearance_area_sqft"] == 28.229
    assert metrics["clearance_bounds"] == [73.0, 47.0, 79.0, 53.0]


def test_inspection_payload_separates_source_from_calculated_values():
    project = load_project(FIXTURE)
    result = find_entity(project, "HOUSE001")

    payload = entity_inspection_payload(result)

    assert payload["category"] == "structure"
    assert payload["source"]["id"] == "HOUSE001"
    assert payload["calculated"]["area_sqft"] == 2475.0
