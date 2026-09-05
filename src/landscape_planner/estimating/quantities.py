"""Deterministic quantity reporting for existing conditions."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from pydantic import BaseModel, Field

from landscape_planner.model.project import LandscapeProject


QUANTITY_SCHEMA_VERSION = "1.0.0"
SUPPORTED_QUANTITY_SCHEMA_VERSIONS = (QUANTITY_SCHEMA_VERSION,)
QUANTITY_SCHEMA_MIGRATION_NOTES = {
    "1.0.0": "Initial stable quantities artifact schema.",
}
DEFAULT_QUANTITIES_DIR = Path("generated") / "quantities"
DEFAULT_QUANTITIES_JSON_PATH = DEFAULT_QUANTITIES_DIR / "existing_conditions_quantities.json"
DEFAULT_QUANTITIES_SCHEMA_PATH = DEFAULT_QUANTITIES_DIR / "existing_conditions_quantities.schema.json"


@dataclass(frozen=True)
class QuantityItem:
    """One calculated quantity tied to a project entity or entity group."""

    category: str
    entity_id: str
    description: str
    quantity: float
    unit: str


class QuantityPayloadItem(BaseModel):
    """One detail row in the versioned quantity artifact."""

    category: str
    entity_id: str
    description: str
    quantity: float
    unit: str


class QuantityPayloadTotal(BaseModel):
    """Summarized quantity group for a category and unit."""

    category: str
    unit: str
    quantity: float


class QuantitiesPayload(BaseModel):
    """Machine-readable artifact schema for deterministic quantity exports."""

    schema_version: str = Field(default=QUANTITY_SCHEMA_VERSION)
    project_id: str
    section: str
    items: tuple[QuantityPayloadItem, ...]
    totals: tuple[QuantityPayloadTotal, ...]


class UnsupportedQuantitiesSchemaVersion(ValueError):
    """Raised when a quantity artifact declares an unsupported schema version."""


def parse_quantities_payload(payload: Mapping[str, object]) -> QuantitiesPayload:
    """Validate a quantities payload and enforce supported schema versions."""

    parsed = QuantitiesPayload.model_validate(payload)
    if parsed.schema_version not in SUPPORTED_QUANTITY_SCHEMA_VERSIONS:
        raise UnsupportedQuantitiesSchemaVersion(
            f"Unsupported quantity artifact schema version: {parsed.schema_version}. "
            f"Supported versions are: {', '.join(SUPPORTED_QUANTITY_SCHEMA_VERSIONS)}. "
            "See docs/adr/0003-schema-versioning-for-future-artifacts.md for migration notes."
        )
    return parsed


def existing_condition_quantities(project: LandscapeProject) -> tuple[QuantityItem, ...]:
    """Calculate existing-conditions quantities from authoritative project geometry."""

    conditions = project.existing_conditions
    items: list[QuantityItem] = [
        QuantityItem(
            "parcel",
            conditions.parcel.id,
            conditions.parcel.name or "Parcel",
            conditions.parcel.area_sqft,
            "sqft",
        )
    ]

    items.extend(
        QuantityItem(
            "structure",
            structure.id,
            structure.name or structure.use,
            structure.area_sqft,
            "sqft",
        )
        for structure in sorted(conditions.structures, key=lambda item: item.id)
    )
    items.extend(
        QuantityItem(
            "hardscape",
            hardscape.id,
            hardscape.name or hardscape.subtype,
            hardscape.area_sqft,
            "sqft",
        )
        for hardscape in sorted(conditions.hardscape, key=lambda item: item.id)
    )
    items.extend(
        QuantityItem(
            "linear_feature",
            feature.id,
            feature.name or feature.subtype,
            feature.length_ft,
            "lf",
        )
        for feature in sorted(conditions.linear_features, key=lambda item: item.id)
    )
    items.extend(
        QuantityItem(
            "planting_bed",
            bed.id,
            bed.name or "Planting bed",
            bed.area_sqft,
            "sqft",
        )
        for bed in sorted(conditions.planting_beds, key=lambda item: item.id)
    )
    items.extend(
        QuantityItem(
            "lawn",
            lawn.id,
            lawn.name or "Lawn",
            lawn.area_sqft,
            "sqft",
        )
        for lawn in sorted(conditions.lawn, key=lambda item: item.id)
    )
    items.append(QuantityItem("tree", "TREES", "Existing trees", len(conditions.trees), "each"))
    items.append(QuantityItem("utility", "UTILITIES", "Utilities", len(conditions.utilities), "each"))
    return tuple(items)


def build_quantities_payload(project: LandscapeProject) -> QuantitiesPayload:
    """Build a deterministic, versioned quantities payload for machine export."""

    items = existing_condition_quantities(project)
    return QuantitiesPayload(
        project_id=project.project_id,
        section="existing_conditions",
        items=tuple(
            QuantityPayloadItem(
                category=item.category,
                entity_id=item.entity_id,
                description=item.description,
                quantity=item.quantity,
                unit=item.unit,
            )
            for item in items
        ),
        totals=tuple(
            QuantityPayloadTotal(category=category, unit=unit, quantity=quantity)
            for (category, unit), quantity in summarize_quantities(items).items()
        ),
    )


def build_quantities_schema() -> dict:
    """Build JSON schema for quantities artifact payloads."""

    return QuantitiesPayload.model_json_schema()


def write_quantities_json(payload: QuantitiesPayload, output_path: str | Path) -> Path:
    """Write deterministic quantity JSON with stable ordering and schema version."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload.model_dump_json(indent=2, by_alias=False) + "\n", encoding="utf-8")
    return output


def write_quantities_schema(schema: dict, output_path: str | Path) -> Path:
    """Write generated JSON schema for downstream tooling."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def summarize_quantities(items: Iterable[QuantityItem]) -> dict[tuple[str, str], float]:
    """Summarize quantities by category and unit."""

    totals: dict[tuple[str, str], float] = {}
    for item in items:
        key = (item.category, item.unit)
        totals[key] = totals.get(key, 0.0) + item.quantity
    return dict(sorted(totals.items()))


def write_quantities_csv(items: Iterable[QuantityItem], output_path: str | Path) -> Path:
    """Write quantity detail and totals to a deterministic CSV file."""

    items = tuple(items)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["section", "category", "entity_id", "description", "quantity", "unit"])
        for item in items:
            writer.writerow(
                [
                    "detail",
                    item.category,
                    item.entity_id,
                    item.description,
                    format_csv_quantity(item.quantity),
                    item.unit,
                ]
            )
        for (category, unit), quantity in summarize_quantities(items).items():
            writer.writerow(["total", category, "", "", format_csv_quantity(quantity), unit])
    return output


def format_csv_quantity(value: float) -> str:
    """Format a quantity for machine-readable CSV without thousands separators."""

    if value == int(value):
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def format_quantity(value: float) -> str:
    """Format a calculated quantity without false precision."""

    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}"
