from pathlib import Path

from typer.testing import CliRunner

from landscape_planner.cli.main import app
from landscape_planner.analysis.validation import validate_project
from landscape_planner.io.yaml_loader import load_project
from landscape_planner.rendering.svg import render_existing_conditions_svg


FIXTURE = Path("tests/fixtures/synthetic")
RUNNER = CliRunner()


def test_synthetic_project_loads_and_validates():
    project = load_project(FIXTURE)
    result = validate_project(project)

    assert result.ok
    assert project.project_id == "synthetic"
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
