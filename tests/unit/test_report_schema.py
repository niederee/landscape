from pathlib import Path

from landscape_planner.analysis.reporting import (
    REPORT_SCHEMA_VERSION,
    build_report_payload,
    build_report_schema,
)
from landscape_planner.analysis.validation import validate_project
from landscape_planner.io.yaml_loader import load_project


FIXTURE = Path("tests/fixtures/synthetic")


def test_report_payload_schema_version_is_stable():
    project = load_project(FIXTURE)
    payload = build_report_payload(project, validate_project(project))

    assert payload.schema_version == REPORT_SCHEMA_VERSION
    assert payload.schema_version == "1.0.0"


def test_report_schema_contract_is_versioned_stable():
    schema = build_report_schema()

    assert schema["title"] == "ReportPayload"
    assert schema["properties"]["schema_version"]["default"] == REPORT_SCHEMA_VERSION
    assert set(schema["required"]) == {
        "project_id",
        "validation",
        "entity_counts",
        "quantity_totals",
        "references",
    }
