"""Stable entity lookup helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from landscape_planner.model.project import (
    Entity,
    HardscapeArea,
    LandscapeProject,
    LawnArea,
    LinearFeature,
    Parcel,
    PlantingBed,
    ReferenceDocument,
    SitePhoto,
    Structure,
    Tree,
    UtilityFeature,
)


@dataclass(frozen=True)
class InspectedEntity:
    """An entity located by stable project ID."""

    category: str
    entity: Entity


def find_entity(project: LandscapeProject, entity_id: str) -> InspectedEntity | None:
    """Find one entity by stable ID."""

    for candidate in iter_inspectable_entities(project):
        if candidate.entity.id == entity_id:
            return candidate
    return None


def iter_inspectable_entities(project: LandscapeProject) -> Iterable[InspectedEntity]:
    """Iterate over inspectable project entities in deterministic order."""

    for document in sorted(project.reference_documents, key=lambda item: item.id):
        yield InspectedEntity("reference_document", document)
    for photo in sorted(project.site_photos, key=lambda item: item.id):
        yield InspectedEntity("site_photo", photo)

    conditions = project.existing_conditions
    yield InspectedEntity("parcel", conditions.parcel)
    for structure in sorted(conditions.structures, key=lambda item: item.id):
        yield InspectedEntity("structure", structure)
        for door in sorted(structure.doors, key=lambda item: item.id):
            yield InspectedEntity("door", door)
    for hardscape in sorted(conditions.hardscape, key=lambda item: item.id):
        yield InspectedEntity("hardscape", hardscape)
    for feature in sorted(conditions.linear_features, key=lambda item: item.id):
        yield InspectedEntity("linear_feature", feature)
    for tree in sorted(conditions.trees, key=lambda item: item.id):
        yield InspectedEntity("tree", tree)
    for bed in sorted(conditions.planting_beds, key=lambda item: item.id):
        yield InspectedEntity("planting_bed", bed)
    for lawn in sorted(conditions.lawn, key=lambda item: item.id):
        yield InspectedEntity("lawn", lawn)
    for utility in sorted(conditions.utilities, key=lambda item: item.id):
        yield InspectedEntity("utility", utility)


def entity_display_name(inspected: InspectedEntity) -> str:
    """Return a concise display name for an inspected entity."""

    entity = inspected.entity
    if entity.name:
        return entity.name
    if isinstance(entity, ReferenceDocument):
        return entity.filename
    if isinstance(entity, SitePhoto):
        return entity.description or entity.filename
    if isinstance(entity, Structure):
        return entity.use
    if isinstance(entity, HardscapeArea):
        return entity.subtype
    if isinstance(entity, LinearFeature):
        return entity.subtype
    if isinstance(entity, Tree):
        return entity.common_name or entity.species or ""
    if isinstance(entity, UtilityFeature):
        return entity.utility_type
    return ""


def entity_to_dict(entity: BaseModel) -> dict:
    """Serialize a Pydantic entity for inspection output."""

    return entity.model_dump(mode="json", by_alias=True, exclude_none=True)


def entity_inspection_payload(inspected: InspectedEntity) -> dict:
    """Build an inspection payload that separates source data from calculations."""

    payload = {
        "category": inspected.category,
        "source": entity_to_dict(inspected.entity),
    }
    calculated = calculated_metrics(inspected.entity)
    if calculated:
        payload["calculated"] = calculated
    return payload


def calculated_metrics(entity: BaseModel) -> dict:
    """Return deterministic calculated metrics for geometric entities."""

    shape = _entity_shape(entity)
    if shape is None:
        return {}

    metrics: dict[str, object] = {
        "geometry_type": shape.geom_type,
        "bounds": [_round(value) for value in shape.bounds],
    }
    if not isinstance(shape, Point):
        metrics["centroid"] = [_round(shape.centroid.x), _round(shape.centroid.y)]
    if shape.area > 0:
        metrics["area_sqft"] = _round(shape.area)
    if shape.length > 0:
        unit = "perimeter_ft" if shape.geom_type in {"Polygon", "MultiPolygon"} else "length_ft"
        metrics[unit] = _round(shape.length)

    if isinstance(entity, Tree):
        canopy = entity.point.buffer(entity.canopy_radius_ft)
        metrics["canopy_area_sqft"] = _round(canopy.area)
        metrics["canopy_radius_ft"] = _round(entity.canopy_radius_ft)
    if isinstance(entity, UtilityFeature) and entity.clearance_shape is not None:
        clearance = entity.clearance_shape
        metrics["clearance_area_sqft"] = _round(clearance.area)
        metrics["clearance_bounds"] = [_round(value) for value in clearance.bounds]
    return metrics


def _entity_shape(entity: BaseModel) -> BaseGeometry | None:
    if isinstance(entity, Parcel):
        return entity.boundary.to_shape()
    if isinstance(entity, Structure):
        return entity.footprint.to_shape()
    if isinstance(entity, (HardscapeArea, LinearFeature, PlantingBed, LawnArea)):
        return entity.geometry.to_shape()
    if isinstance(entity, Tree):
        return entity.point
    if isinstance(entity, UtilityFeature):
        return entity.shape
    if isinstance(entity, SitePhoto):
        return entity.camera_point
    return None


def _round(value: float) -> float:
    return round(value, 3)
