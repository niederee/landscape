"""Project validation rules for the first existing-conditions milestone."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable

from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity

from landscape_planner.model.project import Entity, LandscapeProject
from landscape_planner.analysis.constraints import constraint_shape


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


def validate_project(
    project: LandscapeProject,
    *,
    project_root: Path | None = None,
) -> ValidationResult:
    """Run deterministic validation rules against a project."""

    messages: list[ValidationMessage] = []
    conditions = project.existing_conditions
    parcel_shape = conditions.parcel.boundary.to_shape()
    if project_root is not None:
        messages.extend(_validate_reference_asset_files(project, _resolve_project_root(project_root)))

    messages.extend(_validate_unique_ids(project))
    messages.extend(_validate_source_references(project))
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
        if shape.geom_type != "LineString":
            messages.append(ValidationMessage(
                "ERROR", "EXPECTED_LINESTRING",
                f"{feature.id} line geometry must be a LineString, got {shape.geom_type}.",
                feature.id,
            ))
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
                    "WARNING" if (
                        feature.status == "existing" and feature.subtype == "fence"
                        and feature.placement == "context"
                    ) else "ERROR",
                    "EXISTING_FENCE_OUTSIDE_PARCEL" if (
                        feature.status == "existing" and feature.subtype == "fence"
                        and feature.placement == "context"
                    ) else "GEOMETRY_OUTSIDE_PARCEL",
                    f"{feature.id} line geometry is not fully within the parcel boundary."
                    + (" Context fence alignment does not define ownership or setbacks."
                       if feature.status == "existing" and feature.subtype == "fence"
                       and feature.placement == "context" else ""),
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

    messages.extend(_validate_site_constraints(project))
    return ValidationResult(tuple(messages))


def count_entities(project: LandscapeProject) -> dict[str, int]:
    """Return deterministic entity counts for CLI reporting."""

    conditions = project.existing_conditions
    return {
        "Reference documents": len(project.reference_documents),
        "Site photos": len(project.site_photos),
        "Parcel": 1,
        "Site constraints": len(conditions.site_constraints),
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
    yield from project.reference_documents
    yield from project.site_photos
    conditions = project.existing_conditions
    yield conditions.parcel
    yield from conditions.site_constraints
    yield from conditions.structures
    for structure in conditions.structures:
        yield from structure.doors
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


def _validate_source_references(project: LandscapeProject) -> Iterable[ValidationMessage]:
    known_references = {
        item
        for document in project.reference_documents
        for item in (document.id, document.filename)
    }
    known_references.update(
        item
        for photo in project.site_photos
        for item in (photo.id, photo.filename)
    )
    for entity in _iter_entities(project):
        if entity.source is None or entity.source.reference is None:
            continue
        if entity.source.reference not in known_references:
            yield ValidationMessage(
                "ERROR",
                "UNKNOWN_SOURCE_REFERENCE",
                f"{entity.id} source references {entity.source.reference}, but it is not declared.",
                entity.id,
            )


def _validate_reference_asset_files(project: LandscapeProject, project_root: Path) -> tuple[ValidationMessage, ...]:
    messages: list[ValidationMessage] = []

    for document in project.reference_documents:
        if not _reference_file_exists(project_root, document.filename):
            messages.append(
                ValidationMessage(
                    "WARNING",
                    "REFERENCE_DOCUMENT_NOT_FOUND",
                    f"Reference document {document.id} references missing file: {document.filename}",
                    document.id,
                )
            )

    for photo in project.site_photos:
        if not _reference_file_exists(project_root, photo.filename):
            messages.append(
                ValidationMessage(
                    "WARNING",
                    "SITE_PHOTO_NOT_FOUND",
                    f"Site photo {photo.id} references missing file: {photo.filename}",
                    photo.id,
                )
            )

    return tuple(messages)


def _resolve_project_root(project_path: Path) -> Path:
    return project_path if project_path.is_dir() else project_path.parent


def _reference_file_exists(project_root: Path, filename: str) -> bool:
    path = Path(filename)
    if path.is_absolute():
        return path.exists()
    return (project_root / path).exists()


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


def _validate_site_constraints(project: LandscapeProject) -> Iterable[ValidationMessage]:
    """Evaluate supplied exclusions only; do not infer permitting requirements."""
    conditions = project.existing_conditions
    parcel = conditions.parcel.boundary.to_shape()
    for constraint in conditions.site_constraints:
        yield ValidationMessage(
            "WARNING", "SITE_CONSTRAINT_UNVERIFIED",
            f"{constraint.id} is a supplied project constraint; its applicability and "
            "source interpretation have not been independently verified.", constraint.id,
        )
        try:
            shape = constraint_shape(constraint, conditions.parcel.boundary)
            if shape.geom_type not in {"Polygon", "MultiPolygon"} or not shape.is_valid or shape.area <= 0:
                raise ValueError("Exclusion zone must be a valid positive-area polygon or multipolygon.")
        except ValueError as exc:
            yield ValidationMessage("ERROR", "INVALID_SITE_CONSTRAINT", str(exc), constraint.id)
            continue
        # GEOS intersection can place vertices a few ulps across an oblique
        # boundary. Compare outside area so an already-clipped setback does
        # not fail an exact topological predicate due to floating point noise.
        area_tolerance = max(1e-8, parcel.area * 1e-12)
        if parcel.is_valid and shape.difference(parcel).area > area_tolerance:
            yield ValidationMessage(
                "ERROR", "SITE_CONSTRAINT_OUTSIDE_PARCEL",
                f"{constraint.id} exclusion zone extends outside the parcel boundary.", constraint.id,
            )
        applicable_subtypes = {subtype.strip().casefold() for subtype in constraint.applies_to}
        for target in sorted(conditions.hardscape, key=lambda item: item.id):
            if target.subtype.strip().casefold() not in applicable_subtypes:
                continue
            target_shape = target.geometry.to_shape()
            if not target_shape.is_valid or target_shape.geom_type != "Polygon":
                continue  # Reported by the standard geometry rules.
            overlap = shape.intersection(target_shape).area
            if overlap > 0.001:
                proposed = target.status == "proposed"
                yield ValidationMessage(
                    "ERROR" if proposed else "WARNING",
                    "SITE_CONSTRAINT_VIOLATION" if proposed else "EXISTING_SITE_CONSTRAINT_CONFLICT",
                    f"{target.id} overlaps supplied constraint {constraint.id} by {overlap:.2f} sqft."
                    + ("" if proposed else " Existing condition recorded for review."), target.id,
                )
