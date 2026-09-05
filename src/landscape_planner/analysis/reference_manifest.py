"""Versioned machine-readable reference manifest exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from pydantic import BaseModel, Field

from landscape_planner.model.project import LandscapeProject, SitePhoto


REFERENCE_MANIFEST_SCHEMA_VERSION = "1.0.0"
SUPPORTED_REFERENCE_MANIFEST_SCHEMA_VERSIONS = (REFERENCE_MANIFEST_SCHEMA_VERSION,)
REFERENCE_MANIFEST_SCHEMA_MIGRATION_NOTES = {
    "1.0.0": "Initial stable reference manifest artifact schema.",
}
DEFAULT_REFERENCES_DIR = Path("generated") / "references"
DEFAULT_REFERENCES_JSON_PATH = DEFAULT_REFERENCES_DIR / "landscape_references.json"
DEFAULT_REFERENCES_SCHEMA_PATH = DEFAULT_REFERENCES_DIR / "landscape_references.schema.json"


class ReferenceDocumentRow(BaseModel):
    """Project reference-document fields in a stable machine-readable form."""

    id: str
    document_type: str
    filename: str
    name: str
    date: str


class SitePhotoRow(BaseModel):
    """Project site-photo fields in a stable machine-readable form."""

    id: str
    filename: str
    name: str
    date: str
    camera_x: float | None
    camera_y: float | None
    direction_degrees: float | None


class ReferenceManifestPayload(BaseModel):
    """Versioned manifest for reference documents and photos."""

    schema_version: str = Field(default=REFERENCE_MANIFEST_SCHEMA_VERSION)
    project_id: str
    reference_documents: tuple[ReferenceDocumentRow, ...]
    site_photos: tuple[SitePhotoRow, ...]


class UnsupportedReferenceManifestSchemaVersion(ValueError):
    """Raised when a reference manifest declares an unsupported schema version."""


def parse_reference_manifest_payload(payload: Mapping[str, object]) -> ReferenceManifestPayload:
    """Validate a reference manifest payload and enforce supported schema versions."""

    parsed = ReferenceManifestPayload.model_validate(payload)
    if parsed.schema_version not in SUPPORTED_REFERENCE_MANIFEST_SCHEMA_VERSIONS:
        raise UnsupportedReferenceManifestSchemaVersion(
            f"Unsupported reference manifest schema version: {parsed.schema_version}. "
            f"Supported versions are: {', '.join(SUPPORTED_REFERENCE_MANIFEST_SCHEMA_VERSIONS)}. "
            "See docs/adr/0003-schema-versioning-for-future-artifacts.md for migration notes."
        )
    return parsed


def build_reference_manifest(project: LandscapeProject) -> ReferenceManifestPayload:
    """Build a deterministic reference manifest payload from project data."""

    def camera_coords(photo: SitePhoto) -> tuple[float | None, float | None]:
        if photo.camera_location is None:
            return None, None
        return photo.camera_location

    return ReferenceManifestPayload(
        project_id=project.project_id,
        reference_documents=tuple(
            ReferenceDocumentRow(
                id=document.id,
                document_type=document.document_type,
                filename=document.filename,
                name=document.name or "",
                date=document.date.isoformat() if document.date else "",
            )
            for document in sorted(project.reference_documents, key=lambda item: item.id)
        ),
        site_photos=tuple(
            SitePhotoRow(
                id=photo.id,
                filename=photo.filename,
                name=photo.name or "",
                date=photo.date.isoformat() if photo.date else "",
                camera_x=camera_x,
                camera_y=camera_y,
                direction_degrees=photo.direction_degrees,
            )
            for photo in sorted(project.site_photos, key=lambda item: item.id)
            for camera_x, camera_y in (camera_coords(photo),)
        ),
    )


def build_reference_manifest_schema() -> dict:
    """Build JSON schema for reference manifest payloads."""

    return ReferenceManifestPayload.model_json_schema()


def write_reference_manifest_json(payload: ReferenceManifestPayload, output_path: str | Path) -> Path:
    """Write reference manifest JSON with deterministic formatting."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload.model_dump_json(indent=2, by_alias=False) + "\n", encoding="utf-8")
    return output


def write_reference_manifest_schema(schema: dict, output_path: str | Path) -> Path:
    """Write reference manifest schema for downstream validation."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
