"""Geometry primitives backed by Shapely."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry

Coordinate = tuple[float, float]
GeometryType = Literal["point", "linestring", "polygon"]


class GeometryData(BaseModel):
    """Serializable geometry data used by the project YAML schema."""

    model_config = ConfigDict(extra="forbid")

    type: GeometryType
    coordinates: Any = Field(..., description="GeoJSON-like coordinates in project units.")

    @model_validator(mode="after")
    def validate_coordinates(self) -> "GeometryData":
        self.to_shape()
        return self

    def to_shape(self) -> BaseGeometry:
        """Convert the serializable geometry into a Shapely geometry."""

        if self.type == "point":
            x, y = _coordinate(self.coordinates)
            return Point(x, y)
        if self.type == "linestring":
            coords = [_coordinate(item) for item in self.coordinates]
            if len(coords) < 2:
                raise ValueError("LineString geometry requires at least two coordinates.")
            return LineString(coords)
        if self.type == "polygon":
            coords = [_coordinate(item) for item in self.coordinates]
            if len(coords) < 3:
                raise ValueError("Polygon geometry requires at least three coordinates.")
            return Polygon(coords)
        raise ValueError(f"Unsupported geometry type: {self.type}")


def _coordinate(value: Any) -> Coordinate:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"Coordinate must be a two-item sequence, got {value!r}.")
    x, y = value
    return float(x), float(y)


def point_from_coordinate(value: Any) -> Point:
    """Build a Shapely point from a YAML coordinate pair."""

    x, y = _coordinate(value)
    return Point(x, y)

