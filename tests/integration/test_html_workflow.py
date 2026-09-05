"""Exercise HTML export through the same CLI used by homeowners and agents."""

from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner
import yaml

from landscape_planner.cli.main import app


FIXTURE = Path("tests/fixtures/synthetic")
RUNNER = CliRunner()


@pytest.mark.parametrize("as_file", [False, True])
def test_html_default_output_and_share_profile(tmp_path, as_file):
    project_dir = tmp_path / "project"
    shutil.copytree(FIXTURE, project_dir)
    source = project_dir / "project.yaml" if as_file else project_dir
    result = RUNNER.invoke(app, ["render", str(source), "--format", "html"])
    assert result.exit_code == 0, result.output
    output = project_dir / "generated/html/L1.0_existing_conditions.html"
    document = output.read_text()
    assert "<svg" in document
    assert "Synthetic Residential Test Property" not in document
    assert "Trophy Club" not in document
    assert "references/survey/synthetic_property_survey.pdf" not in document
    # Missing assets are warnings; the offline export remains useful.
    assert "REFERENCE_DOCUMENT_NOT_FOUND" in document


@pytest.mark.parametrize("profile", ["share", "private"])
def test_html_cli_explicit_output_is_repeatable(tmp_path, profile):
    output = tmp_path / "nested/plan.html"
    arguments = ["render", str(FIXTURE), "--format", "html", "--profile", profile,
                 "--output", str(output)]
    result = RUNNER.invoke(app, arguments)
    assert result.exit_code == 0, result.output
    first = output.read_bytes()
    assert RUNNER.invoke(app, arguments).exit_code == 0
    assert output.read_bytes() == first
    assert (b"Synthetic Residential Test Property" in first) == (profile == "private")


def test_html_validation_failure_preserves_existing_output(tmp_path):
    data = yaml.safe_load((FIXTURE / "project.yaml").read_text())
    data["existing_conditions"]["structures"][0]["footprint"]["coordinates"] = [
        [200, 200], [210, 200], [210, 210], [200, 210]
    ]
    source = tmp_path / "project.yaml"
    source.write_text(yaml.safe_dump(data))
    output = tmp_path / "plan.html"
    output.write_text("previous export")
    result = RUNNER.invoke(app, ["render", str(source), "--format", "html", "-o", str(output)])
    assert result.exit_code == 1
    assert "GEOMETRY_OUTSIDE_PARCEL" in result.output
    assert output.read_text() == "previous export"


@pytest.mark.parametrize("alias", [None, "symlink", "hardlink"])
def test_html_refuses_to_overwrite_project_input(tmp_path, alias):
    project_dir = tmp_path / "project"
    shutil.copytree(FIXTURE, project_dir)
    source = project_dir / "project.yaml"
    original = source.read_bytes()
    output = source
    if alias:
        output = tmp_path / "looks-like-an-export.html"
        if alias == "symlink":
            output.symlink_to(source)
        else:
            output.hardlink_to(source)
    result = RUNNER.invoke(app, ["render", str(project_dir), "--format", "html", "-o", str(output)])
    assert result.exit_code != 0
    assert source.read_bytes() == original


@pytest.mark.parametrize("arguments", [["--format", "pdf"], ["--format", "html", "--profile", "public"]])
def test_html_cli_rejects_unsupported_options_without_output(tmp_path, arguments):
    output = tmp_path / "plan.html"
    result = RUNNER.invoke(app, ["render", str(FIXTURE), *arguments, "-o", str(output)])
    assert result.exit_code == 2
    assert not output.exists()
