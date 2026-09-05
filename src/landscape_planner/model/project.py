"""Pydantic project models for existing-conditions landscape data."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from landscape_planner.model.geometry import Coordinate, GeometryData, point_from_coordinate

Confidence = Literal["high", "medium", "low"]
SourceType = Literal[
    "survey",
    "field_measurement",
    "gps",
    "aerial",
    "photo_estimate",
    "manual_estimate",
    "contractor_plan",
    "record_drawing",
    "inferred",
    "unknown",
]
LifecycleStatus = Literal["existing", "proposed"]


class SourceInfo(BaseModel):
    """Measurement provenance for project data."""

    model_config = ConfigDict(extra="forbid")

    type: SourceType = "unknown"
    reference: str | None = None
    confidence: Confidence = "low"
    estimated_accuracy_ft: float | None = None


class Entity(BaseModel):
    """Common fields shared by persistent project entities."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: SourceInfo | None = None
    notes: list[str] = Field(default_factory=list)


class CoordinateSystem(BaseModel):
    """Local coordinate-system metadata."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["local_cartesian"] = "local_cartesian"
    horizontal_units: Literal["ft"] = "ft"
    origin_description: str = "southwest_property_corner"
    north_rotation_degrees: float = 0.0


class Jurisdiction(BaseModel):
    """Local jurisdiction metadata kept as project data."""

    model_config = ConfigDict(extra="forbid")

    city: str | None = None
    state: str | None = None
    country: str | None = "US"


class ProjectLocation(BaseModel):
    """Non-sensitive location metadata."""

    model_config = ConfigDict(extra="forbid")

    city: str | None = None
    state: str | None = None
    country: str | None = "US"


class ProjectUnits(BaseModel):
    """Display and calculation units."""

    model_config = ConfigDict(extra="forbid")

    distance: Literal["ft"] = "ft"
    area: Literal["sqft"] = "sqft"


class LandscapeProjectInfo(BaseModel):
    """Top-level project metadata."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    location: ProjectLocation = Field(default_factory=ProjectLocation)
    units: ProjectUnits = Field(default_factory=ProjectUnits)


class Parcel(Entity):
    """A legal parcel represented by a project boundary polygon."""

    boundary: GeometryData
    easements: list[GeometryData] = Field(default_factory=list)
    setbacks: list[GeometryData] = Field(default_factory=list)
    rights_of_way: list[GeometryData] = Field(default_factory=list)
    legal_notes: list[str] = Field(default_factory=list)

    @property
    def area_sqft(self) -> float:
        return self.boundary.to_shape().area


class Door(Entity):
    """Exterior access point used later for circulation analysis."""

    location: Coordinate
    exterior_direction: str | None = None
    use: str | None = None

    @property
    def point(self) -> Point:
        return point_from_coordinate(self.location)


class Structure(Entity):
    """Building or structure footprint."""

    footprint: GeometryData
    use: str
    status: LifecycleStatus = "existing"
    height_ft: float | None = None
    floor_elevation_ft: float | None = None
    doors: list[Door] = Field(default_factory=list)

    @property
    def area_sqft(self) -> float:
        return self.footprint.to_shape().area


class HardscapeArea(Entity):
    """Paved, decked, gravel, or otherwise hardscape area."""

    geometry: GeometryData
    subtype: str
    material: str | None = None
    status: LifecycleStatus = "existing"
    surface_type: str | None = None
    permeable: bool | None = None
    phase: str | None = None

    @property
    def area_sqft(self) -> float:
        return self.geometry.to_shape().area

    @property
    def perimeter_ft(self) -> float:
        return self.geometry.to_shape().length


class LinearFeature(Entity):
    """Fence, edging, wall, or another linear site feature."""

    geometry: GeometryData
    subtype: str
    material: str | None = None
    status: LifecycleStatus = "existing"
    phase: str | None = None

    @property
    def length_ft(self) -> float:
        return self.geometry.to_shape().length


class Tree(Entity):
    """Existing or proposed tree with canopy geometry."""

    location: Coordinate
    species: str | None = None
    common_name: str | None = None
    trunk_diameter_in: float | None = None
    canopy_radius_ft: float
    height_ft: float | None = None
    condition: str | None = None
    disposition: Literal["preserve", "remove", "relocate", "evaluate"] = "preserve"
    evergreen: bool | None = None
    status: LifecycleStatus = "existing"

    @property
    def point(self) -> Point:
        return point_from_coordinate(self.location)


class PlantingBed(Entity):
    """Planting bed geometry and basic horticultural attributes."""

    geometry: GeometryData
    light_condition: str | None = None
    water_requirement: str | None = None
    soil_condition: str | None = None
    design_style: str | None = None
    irrigation: str | None = None
    mulch: str | None = None
    status: LifecycleStatus = "existing"

    @property
    def area_sqft(self) -> float:
        return self.geometry.to_shape().area

    @property
    def perimeter_ft(self) -> float:
        return self.geometry.to_shape().length


class LawnArea(Entity):
    """Lawn area modeled separately from planting beds."""

    geometry: GeometryData
    species: str | None = None
    sun_condition: str | None = None
    irrigation: str | None = None
    condition: str | None = None
    status: LifecycleStatus = "existing"

    @property
    def area_sqft(self) -> float:
        return self.geometry.to_shape().area


class UtilityFeature(Entity):
    """Utility equipment or service feature with optional clearance geometry."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    utility_type: str = Field(alias="type")
    location: Coordinate | None = None
    geometry: GeometryData | None = None
    clearance_radius_ft: float | None = None
    clearance_zone: GeometryData | None = None
    visibility: str | None = None
    access_requirement: str | None = None
    status: LifecycleStatus = "existing"

    @model_validator(mode="after")
    def validate_location_or_geometry(self) -> "UtilityFeature":
        if self.location is None and self.geometry is None:
            raise ValueError("UtilityFeature requires either location or geometry.")
        if self.location is not None and self.geometry is not None:
            raise ValueError("UtilityFeature must use either location or geometry, not both.")
        if self.clearance_radius_ft is not None and self.clearance_radius_ft <= 0:
            raise ValueError("clearance_radius_ft must be positive when provided.")
        return self

    @property
    def shape(self) -> BaseGeometry:
        if self.geometry is not None:
            return self.geometry.to_shape()
        return point_from_coordinate(self.location)

    @property
    def point(self) -> Point | None:
        shape = self.shape
        if isinstance(shape, Point):
            return shape
        return None

    @property
    def clearance_shape(self) -> BaseGeometry | None:
        if self.clearance_zone is not None:
            return self.clearance_zone.to_shape()
        if self.clearance_radius_ft is not None:
            return self.shape.buffer(self.clearance_radius_ft)
        return None


class ExistingConditions(BaseModel):
    """Current site entities before proposed design work begins."""

    model_config = ConfigDict(extra="forbid")

    parcel: Parcel
    structures: list[Structure] = Field(default_factory=list)
    hardscape: list[HardscapeArea] = Field(default_factory=list)
    linear_features: list[LinearFeature] = Field(default_factory=list)
    trees: list[Tree] = Field(default_factory=list)
    planting_beds: list[PlantingBed] = Field(default_factory=list)
    lawn: list[LawnArea] = Field(default_factory=list)
    utilities: list[UtilityFeature] = Field(default_factory=list)


class LandscapeProject(BaseModel):
    """A complete landscape project at schema version 1."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    project: LandscapeProjectInfo
    coordinate_system: CoordinateSystem = Field(default_factory=CoordinateSystem)
    jurisdiction: Jurisdiction | None = None
    existing_conditions: ExistingConditions

    @property
    def project_id(self) -> str:
        return self.project.id
