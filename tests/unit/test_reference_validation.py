from pathlib import Path

from landscape_planner.analysis.validation import validate_project
from landscape_planner.io.yaml_loader import load_project


FIXTURE = Path("tests/fixtures/synthetic")


def test_declared_reference_document_can_be_used_by_source_info():
    project = load_project(FIXTURE)

    assert project.existing_conditions.parcel.source.reference == "REF_SURVEY_SYNTHETIC"
    assert validate_project(project).ok


def test_unknown_source_reference_is_validation_error():
    project = load_project(FIXTURE).model_copy(deep=True)
    project.existing_conditions.parcel.source.reference = "MISSING_REFERENCE"

    result = validate_project(project)

    assert not result.ok
    assert any(message.code == "UNKNOWN_SOURCE_REFERENCE" for message in result.errors)


def test_photo_camera_point_is_optional_geometry():
    project = load_project(FIXTURE)
    photo = project.site_photos[0]

    assert photo.camera_point.x == 42
    assert photo.camera_point.y == 80
