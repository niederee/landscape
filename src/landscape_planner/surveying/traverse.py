"""Reconstruct supplied survey courses without adjusting or inferring measurements."""

from __future__ import annotations

import math
from pathlib import Path
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator
from shapely.geometry import Polygon
from shapely.validation import explain_validity
import yaml

from landscape_planner.model.geometry import GeometryData

PositiveFeet = Annotated[FiniteFloat, Field(gt=0)]
NonnegativeFeet = Annotated[FiniteFloat, Field(ge=0)]


def _bearing_direction(bearing: str) -> tuple[float, float]:
    """Return east/north unit components for a strict quadrant bearing."""
    value = bearing.strip().upper().replace("′", "'").replace("″", '"')
    cardinals = {"N": (0.0, 1.0), "E": (1.0, 0.0),
                 "S": (0.0, -1.0), "W": (-1.0, 0.0)}
    if value in cardinals:
        return cardinals[value]
    match = re.fullmatch(r"([NS])\s*(.*?)\s*([EW])", value)
    if not match:
        raise ValueError(f"Invalid bearing {bearing!r}; use N21°30'00\"W or N 21.5 W.")
    north_south, angle, east_west = match.groups()
    decimal = re.fullmatch(r"(\d+(?:\.\d+)?)\s*°?", angle)
    dms = re.fullmatch(r"(\d+)\s*°\s*(\d+)\s*'\s*(\d+(?:\.\d+)?)\s*\"", angle)
    if dms is None:
        dms = re.fullmatch(r"(\d+)\s+(\d+)\s+(\d+(?:\.\d+)?)", angle)
    if decimal:
        degrees = float(decimal.group(1))
    elif dms:
        deg, minutes, seconds = map(float, dms.groups())
        if minutes >= 60 or seconds >= 60:
            raise ValueError("Bearing minutes and seconds must each be less than 60.")
        degrees = deg + minutes / 60 + seconds / 3600
    else:
        raise ValueError(f"Invalid angle in bearing {bearing!r}.")
    if not math.isfinite(degrees) or not 0 <= degrees <= 90:
        raise ValueError("Quadrant bearing angle must be between 0 and 90 degrees.")
    radians = math.radians(degrees)
    east = math.sin(radians) * (1 if east_west == "E" else -1)
    north = math.cos(radians) * (1 if north_south == "N" else -1)
    return east, north


class SurveyLeg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bearing: str
    distance_ft: PositiveFeet

    @field_validator("bearing")
    @classmethod
    def valid_bearing(cls, value: str) -> str:
        _bearing_direction(value)
        return value


class SurveyTraverse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    origin: tuple[FiniteFloat, FiniteFloat] = (0.0, 0.0)
    legs: list[SurveyLeg] = Field(min_length=3)
    max_closure_error_ft: NonnegativeFeet = 0.1
    source: str | None = None


class TraverseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    accepted: bool
    boundary: GeometryData | None
    closure_error_ft: FiniteFloat
    closure_dx_ft: FiniteFloat
    closure_dy_ft: FiniteFloat
    closure_ratio: NonnegativeFeet
    perimeter_ft: PositiveFeet
    diagnostics: list[str]
    traverse: SurveyTraverse


def load_traverse(path: str | Path) -> SurveyTraverse:
    """Read a YAML or JSON traverse using YAML's safe loader."""
    return SurveyTraverse.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def reconstruct_traverse(spec: SurveyTraverse) -> TraverseResult:
    """Build a candidate boundary only if closure and polygon checks pass.

    Coordinates use feet, positive x east and positive y north. Courses are not
    balanced: the original last vertex is retained and the ring closes to origin.
    """
    spec = SurveyTraverse.model_validate(spec.model_dump())
    vertices = [tuple(spec.origin)]
    dxs: list[float] = []
    dys: list[float] = []
    try:
        for leg in spec.legs:
            east, north = _bearing_direction(leg.bearing)
            dxs.append(east * leg.distance_ft)
            dys.append(north * leg.distance_ft)
            vertices.append((spec.origin[0] + math.fsum(dxs),
                             spec.origin[1] + math.fsum(dys)))
        dx, dy = math.fsum(dxs), math.fsum(dys)
        perimeter = math.fsum(leg.distance_ft for leg in spec.legs)
        error = math.hypot(dx, dy)
    except (OverflowError, ValueError) as exc:
        raise ValueError("Traverse arithmetic exceeded finite coordinate limits.") from exc
    if not all(math.isfinite(v) for point in vertices for v in point) or not all(
        math.isfinite(v) for v in (dx, dy, perimeter, error)
    ):
        raise ValueError("Traverse arithmetic exceeded finite coordinate limits.")

    diagnostics = ["Mathematical closure does not verify survey accuracy, ownership, or setbacks."]
    accepted = error <= spec.max_closure_error_ft
    if not accepted:
        diagnostics.append(
            f"Closure error {error:.6g} ft exceeds tolerance {spec.max_closure_error_ft:.6g} ft."
        )
    polygon = Polygon(vertices)
    if not polygon.is_valid or polygon.area <= 0 or not math.isfinite(polygon.area):
        accepted = False
        diagnostics.append(f"Invalid boundary polygon: {explain_validity(polygon)}; area={polygon.area}.")
    boundary = None
    if accepted:
        # Explicit closure retains every supplied course rather than distributing error.
        ring = vertices if vertices[-1] == vertices[0] else [*vertices, vertices[0]]
        boundary = GeometryData(type="polygon", coordinates=ring)
        diagnostics.append(
            "Courses are unadjusted; any residual gap is represented by a closing segment."
        )
    return TraverseResult(
        accepted=accepted, boundary=boundary, closure_error_ft=error,
        closure_dx_ft=dx, closure_dy_ft=dy, closure_ratio=error / perimeter,
        perimeter_ft=perimeter, diagnostics=diagnostics, traverse=spec,
    )
