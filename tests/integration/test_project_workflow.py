from pathlib import Path

from typer.testing import CliRunner

from landscape_planner.cli.main import app
from landscape_planner.analysis.validation import validate_project
from landscape_planner.io.yaml_loader import load_project
from landscape_planner.rendering.svg import render_existing_conditions_svg


FIXTURE = Path("tests/fixtures/synthetic")
GREENLEAF = Path("projects/greenleaf")
RUNNER = CliRunner()


def test_synthetic_project_loads_and_validates():
    project = load_project(FIXTURE)
    result = validate_project(project)

    assert result.ok
    assert project.project_id == "synthetic"
    assert len(project.reference_documents) == 1
    assert len(project.site_photos) == 1
    assert project.existing_conditions.parcel.area_sqft == 10400
    assert len(project.existing_conditions.utilities) == 1


def test_existing_conditions_svg_is_deterministic(tmp_path):
    project = load_project(FIXTURE)
    output = tmp_path / "L1.0_existing_conditions.svg"

    render_existing_conditions_svg(project, output)
    first = output.read_text(encoding="utf-8")
    render_existing_conditions_svg(project, output)
    second = output.read_text(encoding="utf-8")

    assert first == second
    assert "L1.0" in first
    assert "Existing Conditions" in first
    assert "HOUSE001" in first
    assert "UTIL001" in first


def test_quantities_cli_reports_synthetic_totals():
    result = RUNNER.invoke(app, ["quantities", str(FIXTURE)])

    assert result.exit_code == 0
    assert "Existing Conditions Quantities" in result.output
    assert "HOUSE001" in result.output
    assert "1,642" in result.output


def test_quantities_cli_writes_csv(tmp_path):
    output = tmp_path / "existing_conditions_quantities.csv"

    result = RUNNER.invoke(app, ["quantities", str(FIXTURE), "--format", "csv", "--output", str(output)])

    assert result.exit_code == 0
    assert "Generated:" in result.output
    assert output.exists()
    assert "total,lawn,,,2175,sqft\n" in output.read_text(encoding="utf-8")


def test_references_cli_lists_documents_and_photos():
    result = RUNNER.invoke(app, ["references", str(FIXTURE)])

    assert result.exit_code == 0
    assert "Reference Documents" in result.output
    assert "REF_SURVEY_SYNTHETIC" in result.output
    assert "PHOTO_BACKYARD_001" in result.output


def test_list_entities_cli_lists_stable_ids():
    result = RUNNER.invoke(app, ["list-entities", str(FIXTURE)])

    assert result.exit_code == 0
    assert "Project Entities" in result.output
    assert "PARCEL001" in result.output
    assert "TREE001" in result.output
    assert "UTIL001" in result.output
    assert "Entities: 17" in result.output


def test_list_entities_cli_filters_by_category():
    result = RUNNER.invoke(app, ["list-entities", str(FIXTURE), "--category", "tree"])

    assert result.exit_code == 0
    assert "TREE001" in result.output
    assert "TREE002" in result.output
    assert "TREE003" in result.output
    assert "HOUSE001" not in result.output
    assert "Entities: 3" in result.output


def test_report_cli_includes_counts_quantities_and_references():
    result = RUNNER.invoke(app, ["report", str(FIXTURE)])

    assert result.exit_code == 0
    assert "Project Report:" in result.output
    assert "Validation" in result.output
    assert "Entity Counts" in result.output
    assert "Errors" in result.output
    assert "Existing-Conditions Quantity Totals" in result.output
    assert "Reference Summary" in result.output


def test_report_cli_exports_json():
    result = RUNNER.invoke(app, ["report", str(FIXTURE), "--format", "json"])

    assert result.exit_code == 0
    assert '"project_id": "synthetic"' in result.output


def test_report_cli_exports_csv(tmp_path):
    output = tmp_path / "project_report.csv"
    result = RUNNER.invoke(app, ["report", str(FIXTURE), "--format", "csv", "--output", str(output)])

    assert result.exit_code == 0
    assert "Generated:" in result.output
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "section,category,unit,count,value,entity_id,message_code,message" in text
    assert "validation" in text


def test_greenleaf_project_loads_from_split_files():
    project = load_project(GREENLEAF)
    result = validate_project(project)

    assert result.ok
    assert project.project_id == "greenleaf"
    assert project.reference_documents[0].id == "REF_SURVEY_PENDING"
    assert project.existing_conditions.parcel.source.reference == "REF_SURVEY_PENDING"


def test_inspect_cli_reports_one_entity_as_json():
    result = RUNNER.invoke(app, ["inspect", str(FIXTURE), "TREE001"])

    assert result.exit_code == 0
    assert "tree TREE001" in result.output
    assert '"source": {' in result.output
    assert '"calculated": {' in result.output
    assert '"id": "TREE001"' in result.output
    assert '"common_name": "Live Oak"' in result.output
    assert '"canopy_area_sqft": 530.077' in result.output


def test_inspect_cli_fails_for_missing_entity():
    result = RUNNER.invoke(app, ["inspect", str(FIXTURE), "MISSING"])

    assert result.exit_code == 1
    assert "Entity not found" in result.output
