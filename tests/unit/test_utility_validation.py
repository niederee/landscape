from pathlib import Path

from landscape_planner.analysis.validation import validate_project
from landscape_planner.io.yaml_loader import load_project
from landscape_planner.model.project import UtilityFeature


FIXTURE = Path("tests/fixtures/synthetic")


def test_utility_outside_parcel_is_validation_error():
    project = load_project(FIXTURE).model_copy(deep=True)
    project.existing_conditions.utilities.append(
        UtilityFeature(id="UTIL_OUTSIDE", type="hose_bib", location=(120, 40))
    )

    result = validate_project(project)

    assert not result.ok
    assert any(message.code == "UTILITY_OUTSIDE_PARCEL" for message in result.errors)


def test_utility_clearance_overlap_is_validation_warning():
    project = load_project(FIXTURE).model_copy(deep=True)
    project.existing_conditions.utilities.append(
        UtilityFeature(id="UTIL_CONFLICT", type="electric_meter", location=(15, 34), clearance_radius_ft=5)
    )

    result = validate_project(project)

    assert result.ok
    assert any(message.code == "UTILITY_CLEARANCE_CONFLICT" for message in result.warnings)

