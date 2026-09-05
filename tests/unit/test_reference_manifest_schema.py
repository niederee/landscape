from pathlib import Path

import pytest

from landscape_planner.analysis.reference_manifest import (
    SUPPORTED_REFERENCE_MANIFEST_SCHEMA_VERSIONS,
    REFERENCE_MANIFEST_SCHEMA_VERSION,
    build_reference_manifest,
    build_reference_manifest_schema,
    parse_reference_manifest_payload,
    UnsupportedReferenceManifestSchemaVersion,
)
from landscape_planner.io.yaml_loader import load_project


FIXTURE = Path("tests/fixtures/synthetic")


def test_reference_manifest_schema_version_is_stable():
    project = load_project(FIXTURE)
    payload = build_reference_manifest(project)

    assert payload.schema_version == REFERENCE_MANIFEST_SCHEMA_VERSION
    assert payload.schema_version == "1.0.0"


def test_reference_manifest_schema_contract_is_versioned_stable():
    schema = build_reference_manifest_schema()

    assert schema["title"] == "ReferenceManifestPayload"
    assert schema["properties"]["schema_version"]["default"] == REFERENCE_MANIFEST_SCHEMA_VERSION
    assert set(schema["required"]) == {
        "project_id",
        "reference_documents",
        "site_photos",
    }


def test_reference_manifest_parser_rejects_unknown_schema_versions():
    project = load_project(FIXTURE)
    payload = build_reference_manifest(project).model_dump()
    payload["schema_version"] = "9.9.9"

    with pytest.raises(UnsupportedReferenceManifestSchemaVersion):
        parse_reference_manifest_payload(payload)


def test_reference_manifest_supported_schema_versions_are_explicit():
    assert list(SUPPORTED_REFERENCE_MANIFEST_SCHEMA_VERSIONS) == [REFERENCE_MANIFEST_SCHEMA_VERSION]
