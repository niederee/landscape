"""Project validation rules for the first existing-conditions milestone."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity

from landscape_planner.model.project import Entity, LandscapeProject


@dataclass(frozen=True)
class ValidationMessage:
    """A deterministic validation result message."""

    severity: str
    code: str
    message: str
    entity_id: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    """Collection of validation messages."""

    messages: tuple[ValidationMessage, ...]

    @property
    def errors(self) -> tuple[ValidationMessage, ...]:
        return tuple(message for message in self.messages if message.severity == "ERROR")

    @property
    def warnings(self) -> tuple[ValidationMessage, ...]:
        return tuple(message for message in self.messages if message.severity == "WARNING")

    @property
    def infos(self) -> tuple[ValidationMessage, ...]:
        return tuple(message for message in self.messages if message.severity == "INFO")

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_project(project: LandscapeProject) -> ValidationResult:
    """Run deterministic validation rules against a project."""

    messages: list[ValidationMessage] = []
    conditions = project.existing_conditions
    parcel_shape = conditions.parcel.boundary.to_shape()

    messages.extend(_validate_unique_ids(project))
    messages.extend(_validate_polygon("parcel boundary", conditions.parcel.id, parcel_shape))

    polygon_entities = [
        *[(item.id, "structure footprint", item.footprint.to_shape()) for item in conditions.structures],
        *[(item.id, "hardscape geometry", item.geometry.to_shape()) for item in conditions.hardscape],
        *[(item.id, "planting bed geometry", item.geometry.to_shape()) for item in conditions.planting_beds],
        *[(item.id, "lawn geometry", item.geometry.to_shape()) for item in conditions.lawn],
    ]
    for entity_id, label, shape in polygon_entities:
        messages.extend(_validate_polygon(label, entity_id, shape))
        if not parcel_shape.covers(shape):
            messages.append(
                ValidationMessage(
                    "ERROR",
                    "GEOMETRY_OUTSIDE_PARCEL",
                    f"{entity_id} {label} is not fully within the parcel boundary.",
                    entity_id,
                )
            )

    for feature in conditions.linear_features:
        shape = feature.geometry.to_shape()
        if not shape.is_valid:
            messages.append(
                ValidationMessage(
                    "ERROR",
                    "INVALID_LINE_GEOMETRY",
                    f"{feature.id} line geometry is invalid.",
                    feature.id,
                )
            )
        if not parcel_shape.covers(shape):
            messages.append(
                ValidationMessage(
                    "ERROR",
                    "GEOMETRY_OUTSIDE_PARCEL",
                    f"{feature.id} line geometry is not fully within the parcel boundary.",
                    feature.id,
                )
            )

    for utility in conditions.utilities:
        shape = utility.shape
        if not shape.is_valid:
            messages.append(
                ValidationMessage(
                    "ERROR",
                    "INVALID_UTILITY_GEOMETRY",
                    f"{utility.id} utility geometry is invalid: {explain_validity(shape)}.",
                    utility.id,
                )
            )
        if not parcel_shape.covers(shape):
            messages.append(
                ValidationMessage(
                    "ERROR",
                    "UTILITY_OUTSIDE_PARCEL",
                    f"{utility.id} utility geometry is outside the parcel boundary.",
                    utility.id,
                )
            )
        clearance = utility.clearance_shape
        if clearance is not None:
            messages.extend(_validate_utility_clearance(project, utility.id, clearance))

    for tree in conditions.trees:
        if not parcel_shape.covers(tree.point):
            messages.append(
                ValidationMessage(
                    "ERROR",
                    "TREE_OUTSIDE_PARCEL",
                    f"{tree.id} tree center is outside the parcel boundary.",
                    tree.id,
                )
            )
        for structure in conditions.structures:
            if structure.footprint.to_shape().covers(tree.point):
                messages.append(
                    ValidationMessage(
                        "ERROR",
                        "TREE_INSIDE_STRUCTURE",
                        f"{tree.id} tree center is inside structure {structure.id}.",
                        tree.id,
                    )
                )

    for left, right in combinations(sorted(conditions.hardscape, key=lambda item: item.id), 2):
        overlap_area = left.geometry.to_shape().intersection(right.geometry.to_shape()).area
        if overlap_area > 0.001:
            messages.append(
                ValidationMessage(
                    "WARNING",
                    "HARDSCAPE_OVERLAP",
                    f"{left.id} overlaps {right.id} by {overlap_area:.2f} sqft.",
                    left.id,
                )
            )

    return ValidationResult(tuple(messages))


def count_entities(project: LandscapeProject) -> dict[str, int]:
    """Return deterministic entity counts for CLI reporting."""

    conditions = project.existing_conditions
    return {
        "Parcel": 1,
        "Structures": len(conditions.structures),
        "Hardscape": len(conditions.hardscape),
        "Linear features": len(conditions.linear_features),
        "Trees": len(conditions.trees),
        "Planting beds": len(conditions.planting_beds),
        "Lawn areas": len(conditions.lawn),
        "Utilities": len(conditions.utilities),
    }


def _validate_unique_ids(project: LandscapeProject) -> Iterable[ValidationMessage]:
    seen: dict[str, str] = {}
    for entity in _iter_entities(project):
        if entity.id in seen:
            yield ValidationMessage(
                "ERROR",
                "DUPLICATE_ENTITY_ID",
                f"{entity.id} is used by both {seen[entity.id]} and {entity.__class__.__name__}.",
                entity.id,
            )
        else:
            seen[entity.id] = entity.__class__.__name__


def _iter_entities(project: LandscapeProject) -> Iterable[Entity]:
    conditions = project.existing_conditions
    yield conditions.parcel
    yield from conditions.structures
    yield from conditions.hardscape
    yield from conditions.linear_features
    yield from conditions.trees
    yield from conditions.planting_beds
    yield from conditions.lawn
    yield from conditions.utilities


def _validate_polygon(label: str, entity_id: str, shape: BaseGeometry) -> Iterable[ValidationMessage]:
    if shape.geom_type != "Polygon":
        yield ValidationMessage(
            "ERROR",
            "EXPECTED_POLYGON",
            f"{entity_id} {label} must be a polygon, got {shape.geom_type}.",
            entity_id,
        )
    if not shape.is_valid:
        yield ValidationMessage(
            "ERROR",
            "INVALID_POLYGON",
            f"{entity_id} {label} polygon is invalid: {explain_validity(shape)}.",
            entity_id,
        )
    if shape.area <= 0:
        yield ValidationMessage(
            "ERROR",
            "EMPTY_POLYGON",
            f"{entity_id} {label} polygon has no positive area.",
            entity_id,
        )


def _validate_utility_clearance(
    project: LandscapeProject,
    utility_id: str,
    clearance: BaseGeometry,
) -> Iterable[ValidationMessage]:
    conditions = project.existing_conditions
    parcel_shape = conditions.parcel.boundary.to_shape()
    if not clearance.is_valid:
        yield ValidationMessage(
            "ERROR",
            "INVALID_UTILITY_CLEARANCE",
            f"{utility_id} utility clearance zone is invalid: {explain_validity(clearance)}.",
            utility_id,
        )
    if not parcel_shape.covers(clearance):
        yield ValidationMessage(
            "WARNING",
            "UTILITY_CLEARANCE_OUTSIDE_PARCEL",
            f"{utility_id} utility clearance zone extends outside the parcel boundary.",
            utility_id,
        )

    clearance_targets = [
        *[(item.id, "structure", item.footprint.to_shape()) for item in conditions.structures],
        *[(item.id, "hardscape", item.geometry.to_shape()) for item in conditions.hardscape],
        *[(item.id, "planting bed", item.geometry.to_shape()) for item in conditions.planting_beds],
        *[(item.id, "lawn", item.geometry.to_shape()) for item in conditions.lawn],
    ]
    for target_id, label, target_shape in sorted(clearance_targets, key=lambda item: item[0]):
        overlap_area = clearance.intersection(target_shape).area
        if overlap_area > 0.001:
            yield ValidationMessage(
                "WARNING",
                "UTILITY_CLEARANCE_CONFLICT",
                f"{utility_id} clearance zone overlaps {label} {target_id} by {overlap_area:.2f} sqft.",
                utility_id,
            )
