from pathlib import Path

import pytest

from landscape_planner.estimating.quantities import (
    SUPPORTED_QUANTITY_SCHEMA_VERSIONS,
    QUANTITY_SCHEMA_VERSION,
    build_quantities_payload,
    build_quantities_schema,
    parse_quantities_payload,
    UnsupportedQuantitiesSchemaVersion,
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


def test_quantities_payload_parser_rejects_unknown_schema_versions():
    project = load_project(FIXTURE)
    payload = build_quantities_payload(project).model_dump()
    payload["schema_version"] = "0.9.0"

    with pytest.raises(UnsupportedQuantitiesSchemaVersion):
        parse_quantities_payload(payload)


def test_quantities_supported_schema_versions_are_explicit():
    assert list(SUPPORTED_QUANTITY_SCHEMA_VERSIONS) == [QUANTITY_SCHEMA_VERSION]
