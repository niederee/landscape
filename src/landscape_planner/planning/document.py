"""Explicit planning sidecar; baseline project schema remains unchanged."""
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from landscape_planner.planning.concepts import Concept
from landscape_planner.planning.phases import Phase


class PlanningDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    concepts: list[Concept] = Field(default_factory=list)
    selected_concept: str | None = None
    phases: list[Phase] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_concepts(self):
        ids = [concept.id for concept in self.concepts]
        if len(ids) != len(set(ids)) or "existing" in ids:
            raise ValueError("Concept IDs must be unique and cannot use reserved ID 'existing'.")
        if self.selected_concept is not None and self.selected_concept not in ids:
            raise ValueError("selected_concept must identify a declared concept.")
        phase_ids = [phase.id for phase in self.phases]
        if "existing" in phase_ids:
            raise ValueError("Phase ID 'existing' is reserved.")
        return self


def load_planning(path: str | Path) -> PlanningDocument:
    try:
        with Path(path).open(encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid planning YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Planning YAML must contain a mapping.")
    return PlanningDocument.model_validate(raw)
