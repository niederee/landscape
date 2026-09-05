from pathlib import Path

from landscape_planner.analysis.validation import validate_project
from landscape_planner.io.yaml_loader import load_project
from landscape_planner.rendering.svg import render_existing_conditions_svg


FIXTURE = Path("tests/fixtures/synthetic")


def test_synthetic_project_loads_and_validates():
    project = load_project(FIXTURE)
    result = validate_project(project)

    assert result.ok
    assert project.project_id == "synthetic"
    assert project.existing_conditions.parcel.area_sqft == 10400


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

