"""Run planning sidecars through the public CLI, including safe failure paths."""
from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner
import yaml

from landscape_planner.cli.main import app
from landscape_planner.planning.document import load_planning

RUNNER = CliRunner()


@pytest.fixture
def project_dir(tmp_path):
    target = tmp_path / "project"
    shutil.copytree("examples/synthetic", target, ignore=shutil.ignore_patterns("generated"))
    return target


@pytest.mark.parametrize("command", ["compare", "phases"])
def test_planning_commands_generate_repeatable_reviews_without_mutation(project_dir, tmp_path, command):
    original = {p.name: p.read_bytes() for p in project_dir.glob("*.yaml")}
    output = tmp_path / f"{command}.html"
    args = [command, str(project_dir), "-o", str(output)]
    result = RUNNER.invoke(app, args)
    assert result.exit_code == 0, (result.output, result.exception)
    first = output.read_bytes()
    assert b"REFERENCE_DOCUMENT_NOT_FOUND" in first
    assert b"Synthetic Residential Demo" not in first
    assert RUNNER.invoke(app, args).exit_code == 0
    assert output.read_bytes() == first
    assert original == {p.name: p.read_bytes() for p in project_dir.glob("*.yaml")}


@pytest.mark.parametrize("command", ["compare", "phases", "render"])
def test_planning_inputs_are_protected_even_through_hardlinks(project_dir, tmp_path, command):
    source = project_dir / "planning.yaml"
    original = source.read_bytes()
    output = tmp_path / "alias.html"
    output.hardlink_to(source)
    args = [command, str(project_dir), "-o", str(output)]
    if command == "render":
        args += ["--format", "html"]
    result = RUNNER.invoke(app, args)
    assert result.exit_code == 2
    assert source.read_bytes() == original


def test_invalid_phase_target_preserves_existing_output(project_dir, tmp_path):
    source = project_dir / "planning.yaml"
    raw = yaml.safe_load(source.read_text())
    raw["selected_concept"] = "garden"
    source.write_text(yaml.safe_dump(raw))
    output = tmp_path / "phases.html"
    output.write_text("previous review")
    result = RUNNER.invoke(app, ["phases", str(project_dir), "-o", str(output)])
    assert result.exit_code == 1, (result.output, result.exception)
    assert "Final phase does not match" in result.output
    assert output.read_text() == "previous review"


def test_invalid_planning_yaml_has_clear_error(project_dir, tmp_path):
    (project_dir / "planning.yaml").write_text("concepts: [broken")
    result = RUNNER.invoke(app, ["compare", str(project_dir), "-o", str(tmp_path / "out.html")])
    assert result.exit_code == 1
    assert "Unable to export" in result.output


def test_sidecar_rejects_unknown_selection_and_duplicate_concepts(project_dir):
    path = project_dir / "planning.yaml"
    raw = yaml.safe_load(path.read_text())
    raw["selected_concept"] = "missing"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="selected_concept"):
        load_planning(path)


def test_phase_target_matches_entities_independent_of_collection_order(project_dir, tmp_path):
    path = project_dir / "planning.yaml"
    operations = [
        {"action": "add", "category": "trees", "entity_id": identifier,
         "data": {"location": location, "canopy_radius_ft": 2, "status": "proposed"}}
        for identifier, location in [("NEW_A", [5, 90]), ("NEW_B", [5, 95])]
    ]
    path.write_text(yaml.safe_dump({
        "concepts": [{"id": "target", "name": "Two new trees", "operations": operations}],
        "selected_concept": "target",
        "phases": [{"id": "plant", "name": "Plant trees", "operations": operations[::-1]}],
    }))
    result = RUNNER.invoke(app, ["phases", str(project_dir), "-o", str(tmp_path / "out.html")])
    assert result.exit_code == 0, (result.output, result.exception)
