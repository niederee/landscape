from pathlib import Path

from landscape_planner.inspection import entity_to_dict, find_entity
from landscape_planner.io.yaml_loader import load_project


FIXTURE = Path("tests/fixtures/synthetic")


def test_find_entity_returns_category_and_entity():
    project = load_project(FIXTURE)

    result = find_entity(project, "TREE001")

    assert result is not None
    assert result.category == "tree"
    assert result.entity.id == "TREE001"


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

