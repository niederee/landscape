"""Stable entity lookup helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel

from landscape_planner.model.project import Entity, LandscapeProject


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


def entity_to_dict(entity: BaseModel) -> dict:
    """Serialize a Pydantic entity for inspection output."""

    return entity.model_dump(mode="json", by_alias=True, exclude_none=True)

