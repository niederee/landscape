from pathlib import Path
import shutil

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


def test_validate_project_warns_for_missing_reference_files(tmp_path: Path):
    project_path = tmp_path / "synthetic"
    shutil.copytree(FIXTURE, project_path)

    project = load_project(project_path)
    result = validate_project(project, project_root=project_path)

    assert result.ok
    assert any(message.code == "REFERENCE_DOCUMENT_NOT_FOUND" for message in result.warnings)
    assert any(message.code == "SITE_PHOTO_NOT_FOUND" for message in result.warnings)


def test_validate_project_allows_absolute_reference_paths(tmp_path: Path):
    project_path = tmp_path / "synthetic_abs"
    shutil.copytree(FIXTURE, project_path)
    project = load_project(project_path)

    document = project.reference_documents[0]
    photo = project.site_photos[0]
    document.filename = str(project_path / document.filename)
    photo.filename = str(project_path / photo.filename)

    (project_path / "references/survey").mkdir(parents=True, exist_ok=True)
    (project_path / "references/survey/synthetic_property_survey.pdf").write_text("stub", encoding="utf-8")
    (project_path / "references/photos").mkdir(parents=True, exist_ok=True)
    (project_path / "references/photos/backyard_northwest.jpg").write_text("stub", encoding="utf-8")

    result = validate_project(project, project_root=project_path)
    assert result.ok
    assert not any(message.code == "REFERENCE_DOCUMENT_NOT_FOUND" for message in result.warnings)
    assert not any(message.code == "SITE_PHOTO_NOT_FOUND" for message in result.warnings)
