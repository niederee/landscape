from landscape_planner.analysis.validation import validate_project
from landscape_planner.io.yaml_loader import load_project
from landscape_planner.model.geometry import GeometryData
from landscape_planner.model.project import Door, SourceInfo


def test_nested_door_ids_and_sources_are_validated():
    project = load_project("examples/synthetic")
    project.existing_conditions.structures[0].doors.append(Door(
        id=project.existing_conditions.parcel.id,
        location=(1, 1),
        source=SourceInfo(reference="undeclared"),
    ))
    codes = {message.code for message in validate_project(project).errors}
    assert {"DUPLICATE_ENTITY_ID", "UNKNOWN_SOURCE_REFERENCE"} <= codes


def test_non_line_linear_feature_fails_before_rendering():
    project = load_project("examples/synthetic")
    project.existing_conditions.linear_features[0].geometry = GeometryData(
        type="point", coordinates=[1, 1],
    )
    assert "EXPECTED_LINESTRING" in {
        message.code for message in validate_project(project).errors
    }
