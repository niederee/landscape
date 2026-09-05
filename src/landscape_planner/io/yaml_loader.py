"""YAML loading for landscape project directories."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from landscape_planner.model.project import LandscapeProject


class ProjectLoadError(RuntimeError):
    """Raised when a project directory cannot be loaded."""


def load_project(project_path: str | Path) -> LandscapeProject:
    """Load a landscape project from a directory containing `project.yaml`."""

    path = Path(project_path)
    if path.is_file():
        raw = _read_yaml(path)
    else:
        project_yaml = path / "project.yaml"
        if not project_yaml.exists():
            raise ProjectLoadError(f"Project file not found: {project_yaml}")
        raw = _read_yaml(project_yaml)
        existing_yaml = path / "existing_conditions.yaml"
        if existing_yaml.exists():
            raw["existing_conditions"] = _read_yaml(existing_yaml)
    return LandscapeProject.model_validate(raw)


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ProjectLoadError(f"YAML document must be a mapping: {path}")
    return data

