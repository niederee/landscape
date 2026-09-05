"""Deterministic quantity reporting for existing conditions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from landscape_planner.model.project import LandscapeProject


@dataclass(frozen=True)
class QuantityItem:
    """One calculated quantity tied to a project entity or entity group."""

    category: str
    entity_id: str
    description: str
    quantity: float
    unit: str


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


def summarize_quantities(items: Iterable[QuantityItem]) -> dict[tuple[str, str], float]:
    """Summarize quantities by category and unit."""

    totals: dict[tuple[str, str], float] = {}
    for item in items:
        key = (item.category, item.unit)
        totals[key] = totals.get(key, 0.0) + item.quantity
    return dict(sorted(totals.items()))


def format_quantity(value: float) -> str:
    """Format a calculated quantity without false precision."""

    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}"

