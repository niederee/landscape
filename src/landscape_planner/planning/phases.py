"""Dependency-ordered cumulative work phases and explicitly sourced cost allowances.

Costs summarize only the supplied line items, in USD.
They are not a contractor quote or a complete project budget. No rates are inferred.
"""

from __future__ import annotations

import math
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from landscape_planner.model.project import LandscapeProject
from landscape_planner.planning.concepts import ConceptOperation, apply_operations

Nonblank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Nonnegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class CostItem(BaseModel):
    """An explicit quantity and optional sourced low/high unit-rate allowance."""

    model_config = ConfigDict(extra="forbid")

    id: Nonblank
    name: Nonblank | None = None
    quantity: Nonnegative
    unit: Nonblank
    rate_low: Nonnegative | None = None
    rate_high: Nonnegative | None = None
    source: Nonblank | None = None
    currency: Literal["USD"] = "USD"

    @model_validator(mode="after")
    def validate_rates(self) -> CostItem:
        if (self.rate_low is None) != (self.rate_high is None):
            raise ValueError("rate_low and rate_high must both be supplied or both be unknown")
        if self.rate_low is not None:
            if self.rate_low > self.rate_high:
                raise ValueError("rate_low must not exceed rate_high")
            if not self.source:
                raise ValueError("Known rates require a source")
            if not math.isfinite(self.quantity * self.rate_high):
                raise ValueError("Extended cost must be finite")
        return self


class Phase(BaseModel):
    """An authored phase; dependencies precede it in the cumulative sequence."""

    model_config = ConfigDict(extra="forbid")

    id: Nonblank
    name: Nonblank
    depends_on: list[Nonblank] = Field(default_factory=list)
    operations: list[ConceptOperation] = Field(default_factory=list)
    cost_items: list[CostItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_items(self) -> Phase:
        if len(self.depends_on) != len(set(self.depends_on)):
            raise ValueError("Duplicate phase dependencies")
        ids = [item.id for item in self.cost_items]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate cost item IDs within a phase")
        return self


class CostSummary(BaseModel):
    """Known subtotals; complete refers only to the supplied scope, never all work."""

    known_low: float = 0
    known_high: float = 0
    currency: Literal["USD"] = "USD"
    unknown_item_ids: list[str] = Field(default_factory=list)
    complete: bool = True


class PhaseSnapshot(BaseModel):
    phase: Phase
    project: LandscapeProject
    cost: CostSummary
    cumulative_cost: CostSummary
    warnings: list[str] = Field(default_factory=list)


def _phase_cost(phase: Phase) -> CostSummary:
    low = high = 0.0
    unknown: list[str] = []
    for item in phase.cost_items:
        if item.rate_low is None:
            unknown.append(f"{phase.id}:{item.id}")
        else:
            low += item.quantity * item.rate_low
            high += item.quantity * item.rate_high
    if phase.operations and not phase.cost_items:
        unknown.append(f"{phase.id}:unestimated")
    if not math.isfinite(low) or not math.isfinite(high):
        raise ValueError(f"Cost subtotal for phase {phase.id!r} is not finite")
    return CostSummary(known_low=low, known_high=high, unknown_item_ids=unknown,
                       complete=not unknown)


def resolve_phases(project: LandscapeProject, phases: list[Phase]) -> list[PhaseSnapshot]:
    """Apply all phases cumulatively in stable topological order without mutation.

    Among currently eligible phases, the earliest in the authored list is chosen.
    Each snapshot includes all earlier phases, including independent branches;
    dependencies constrain ordering, rather than selecting alternate designs.
    """
    # Pydantic instances are mutable; validate fresh payloads before calculations.
    phases = [Phase.model_validate(phase.model_dump()) for phase in phases]
    by_id = {phase.id: phase for phase in phases}
    if len(by_id) != len(phases):
        raise ValueError("Duplicate phase IDs")
    for phase in phases:
        missing = set(phase.depends_on) - by_id.keys()
        if missing:
            raise ValueError(f"Phase {phase.id!r} has unknown dependencies: {sorted(missing)}")
    ordered: list[Phase] = []
    remaining = list(phases)
    completed: set[str] = set()
    while remaining:
        next_phase = next((p for p in remaining if set(p.depends_on) <= completed), None)
        if next_phase is None:
            raise ValueError("Cyclic phase dependencies")
        ordered.append(next_phase)
        completed.add(next_phase.id)
        remaining.remove(next_phase)

    snapshots: list[PhaseSnapshot] = []
    current = project.model_copy(deep=True)
    cumulative = CostSummary()
    added: dict[tuple[str, str], str] = {}
    preserved: set[tuple[str, str]] = set()
    for phase in ordered:
        warnings: list[str] = []
        for operation in phase.operations:
            key = (operation.category, operation.entity_id)
            if operation.action in {"update", "remove"}:
                if key in preserved:
                    raise ValueError(f"Phase {phase.id!r} alters preserved entity {key[1]!r}")
                if key in added:
                    warnings.append(
                        f"Potential rework: phase {phase.id!r} will {operation.action} "
                        f"{key[1]!r}, added in phase {added[key]!r}."
                    )
            if operation.action == "add":
                added[key] = phase.id
            elif operation.action == "preserve":
                preserved.add(key)
            elif operation.action == "remove":
                added.pop(key, None)
        current = apply_operations(current, phase.operations)
        cost = _phase_cost(phase)
        unknown = cumulative.unknown_item_ids + cost.unknown_item_ids
        cumulative = CostSummary(
            known_low=cumulative.known_low + cost.known_low,
            known_high=cumulative.known_high + cost.known_high,
            unknown_item_ids=unknown,
            complete=not unknown,
        )
        if not math.isfinite(cumulative.known_low) or not math.isfinite(cumulative.known_high):
            raise ValueError("Cumulative cost subtotal is not finite")
        snapshots.append(PhaseSnapshot(
            phase=phase.model_copy(deep=True), project=current.model_copy(deep=True),
            cost=cost, cumulative_cost=cumulative.model_copy(deep=True), warnings=warnings,
        ))
    return snapshots
