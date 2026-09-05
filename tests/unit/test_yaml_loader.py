from pathlib import Path

import pytest

from landscape_planner.analysis.validation import validate_project
from landscape_planner.io.yaml_loader import ProjectLoadError, load_project


SPLIT_FIXTURE = Path("tests/fixtures/split_references")


def test_project_loader_merges_split_references_file():
    project = load_project(SPLIT_FIXTURE)

    assert project.project_id == "split-references"
    assert project.reference_documents[0].id == "REF_SPLIT_SURVEY"
    assert project.site_photos[0].id == "PHOTO_SPLIT_001"
    assert project.existing_conditions.parcel.source.reference == "REF_SPLIT_SURVEY"
    assert validate_project(project).ok


def test_project_loader_rejects_unknown_references_yaml_keys(tmp_path):
    (tmp_path / "project.yaml").write_text(
        """
schema_version: 1
project:
  id: bad-references
  name: Bad References
existing_conditions:
  parcel:
    id: PARCEL001
    boundary:
      type: polygon
      coordinates:
        - [0, 0]
        - [1, 0]
        - [1, 1]
        - [0, 1]
""",
        encoding="utf-8",
    )
    (tmp_path / "references.yaml").write_text("documents: []\n", encoding="utf-8")

    with pytest.raises(ProjectLoadError, match="unsupported top-level keys: documents"):
        load_project(tmp_path)

