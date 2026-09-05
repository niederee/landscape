from pathlib import Path

from landscape_planner.estimating.quantities import (
    QUANTITY_SCHEMA_VERSION,
    build_quantities_payload,
    build_quantities_schema,
)
from landscape_planner.io.yaml_loader import load_project


FIXTURE = Path("tests/fixtures/synthetic")


def test_quantities_payload_schema_version_is_stable():
    project = load_project(FIXTURE)
    payload = build_quantities_payload(project)

    assert payload.schema_version == QUANTITY_SCHEMA_VERSION
    assert payload.schema_version == "1.0.0"


def test_quantities_schema_contract_is_versioned_stable():
    schema = build_quantities_schema()

    assert schema["title"] == "QuantitiesPayload"
    assert schema["properties"]["schema_version"]["default"] == QUANTITY_SCHEMA_VERSION
    assert set(schema["required"]) == {
        "project_id",
        "items",
        "totals",
        "section",
    }
