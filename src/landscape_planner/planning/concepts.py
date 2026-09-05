"""Resolve authored design changes without mutating the measured baseline."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from landscape_planner.analysis.validation import validate_project
from landscape_planner.estimating.quantities import existing_condition_quantities, summarize_quantities
from landscape_planner.model.project import LandscapeProject

Category = Literal[
    "structures", "hardscape", "linear_features", "trees", "planting_beds", "lawn", "utilities"
]
CATEGORIES = (
    "structures", "hardscape", "linear_features", "trees", "planting_beds", "lawn", "utilities"
)


class ConceptOperation(BaseModel):
    """One explicit change. Updates replace supplied fields, including nested fields."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["add", "update", "remove", "preserve"]
    category: Category
    entity_id: str = Field(min_length=1)
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("entity_id")
    @classmethod
    def nonblank_id(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("entity_id must be nonblank and have no surrounding whitespace")
        return value

    @model_validator(mode="after")
    def valid_data(self) -> "ConceptOperation":
        if self.action in {"remove", "preserve"} and self.data:
            raise ValueError(f"{self.action} must not contain data")
        if "id" in self.data and self.data["id"] != self.entity_id:
            raise ValueError("data.id must equal entity_id; renaming entities is unsupported")
        if self.action == "update" and not (self.data.keys() - {"id"}):
            raise ValueError("update requires at least one field other than id")
        return self


class Concept(BaseModel):
    """A named alternative stored separately from the existing-conditions project."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, pattern=r"^\S(?:.*\S)?$")
    name: str = Field(min_length=1, pattern=r"^\S(?:.*\S)?$")
    description: str | None = None
    operations: list[ConceptOperation] = Field(default_factory=list)


def _all_ids(project: LandscapeProject) -> set[str]:
    conditions = project.existing_conditions
    ids = {conditions.parcel.id}
    ids.update(item.id for item in project.reference_documents)
    ids.update(item.id for item in project.site_photos)
    for category in CATEGORIES:
        ids.update(item.id for item in getattr(conditions, category))
    ids.update(door.id for structure in conditions.structures for door in structure.doors)
    return ids


def apply_operations(
    project: LandscapeProject, operations: Iterable[ConceptOperation]
) -> LandscapeProject:
    """Apply operations in order to a deep copy and reject invalid resolved geometry.

    A preserve operation locks its entity against subsequent mutation in this
    operation sequence. Warnings remain available through ``validate_project``;
    errors prevent returning a snapshot. No parcel or coordinate-frame edits are
    available through this API.
    """

    resolved = LandscapeProject.model_validate(project.model_dump(mode="python"))
    resolved = resolved.model_copy(deep=True)
    preserved: set[str] = set()
    for raw_operation in operations:
        # Revalidate even model instances, which callers could have mutated.
        operation = ConceptOperation.model_validate(
            raw_operation.model_dump() if isinstance(raw_operation, ConceptOperation)
            else raw_operation
        )
        collection = getattr(resolved.existing_conditions, operation.category)
        matches = [index for index, item in enumerate(collection) if item.id == operation.entity_id]
        if len(matches) > 1:
            raise ValueError(f"Ambiguous entity ID: {operation.entity_id}")
        if operation.action == "add":
            if operation.entity_id in _all_ids(resolved):
                raise ValueError(f"Cannot add duplicate entity ID: {operation.entity_id}")
        elif not matches:
            raise ValueError(
                f"Unknown entity {operation.entity_id} in category {operation.category}"
            )
        if operation.action == "preserve":
            preserved.add(operation.entity_id)
            continue
        if operation.entity_id in preserved:
            raise ValueError(f"Cannot mutate preserved entity: {operation.entity_id}")

        payload = resolved.model_dump(mode="python")
        target = payload["existing_conditions"][operation.category]
        if operation.action == "remove":
            target.pop(matches[0])
        elif operation.action == "update":
            target[matches[0]].update(deepcopy(operation.data))
            # Utility models expose both their Python name and the YAML alias.
            if operation.category == "utilities" and "type" in operation.data:
                target[matches[0]].pop("utility_type", None)
        else:
            target.append({**deepcopy(operation.data), "id": operation.entity_id})
        resolved = LandscapeProject.model_validate(payload)

    result = validate_project(resolved)
    if result.errors:
        details = "; ".join(f"{item.code}: {item.message}" for item in result.errors)
        raise ValueError(f"Resolved concept is invalid: {details}")
    return resolved


def resolve_concept(project: LandscapeProject, concept: Concept) -> LandscapeProject:
    """Produce a validated, independent project snapshot for one alternative."""

    return apply_operations(project, concept.operations)


def compare_projects(before: LandscapeProject, after: LandscapeProject) -> dict[str, Any]:
    """Return deterministic entity differences and authoritative quantity deltas.

    ``preserved`` means unchanged collection entities, whether or not an explicit
    preserve operation was used. Quantity rows include unchanged totals so that
    each snapshot's totals can be fully reconciled with the core quantity report.
    """

    def entities(project: LandscapeProject) -> dict[str, tuple[str, dict]]:
        return {
            entity.id: (category, entity.model_dump(mode="json"))
            for category in CATEGORIES
            for entity in getattr(project.existing_conditions, category)
        }

    old, new = entities(before), entities(after)
    shared = old.keys() & new.keys()
    old_totals = summarize_quantities(existing_condition_quantities(before))
    new_totals = summarize_quantities(existing_condition_quantities(after))
    return {
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
        "modified": sorted(key for key in shared if old[key] != new[key]),
        "preserved": sorted(key for key in shared if old[key] == new[key]),
        "quantity_deltas": [
            {
                "category": category,
                "unit": unit,
                "before": old_totals.get((category, unit), 0.0),
                "after": new_totals.get((category, unit), 0.0),
                "delta": new_totals.get((category, unit), 0.0)
                - old_totals.get((category, unit), 0.0),
            }
            for category, unit in sorted(old_totals.keys() | new_totals.keys())
        ],
    }
