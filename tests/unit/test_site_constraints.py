"""Supplied pool restrictions and observed fence alignment are distinct."""

import math

import pytest
from pydantic import ValidationError
from shapely.geometry import Point

from landscape_planner.analysis.constraints import constraint_shape, edge_setback_zone
from landscape_planner.analysis.validation import validate_project
from landscape_planner.model.geometry import GeometryData
from landscape_planner.model.project import (
    ExistingConditions, HardscapeArea, LandscapeProject, LandscapeProjectInfo,
    LinearFeature, Parcel, PlantingBed, SiteConstraint, SourceInfo,
)


def polygon(coords):
    return GeometryData(type="polygon", coordinates=coords)


def rectangle(x1, y1, x2, y2):
    return polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])


def project():
    return LandscapeProject(
        project=LandscapeProjectInfo(id="test", name="Synthetic test"),
        existing_conditions=ExistingConditions(parcel=Parcel(id="parcel", boundary=rectangle(0, 0, 100, 100))),
    )


def test_setback_distance_and_edge_index_follow_parcel_not_fence():
    p = project()
    zone = SiteConstraint(id="rear", edge_index=2, distance_ft=10)
    p.existing_conditions.site_constraints.append(zone)
    p.existing_conditions.linear_features.append(LinearFeature(
        id="fence", geometry=GeometryData(type="linestring", coordinates=[(0, 70), (100, 70)]), subtype="fence",
    ))
    shape = constraint_shape(zone, p.existing_conditions.parcel.boundary)
    assert shape.area == pytest.approx(1000)
    assert shape.bounds == (0, 90, 100, 100)
    assert not shape.covers(Point(50, 80))


def test_oblique_segment_uses_perpendicular_distance_and_round_endpoints():
    parcel = polygon([(0, 0), (10, 10), (0, 30), (-20, 10)])
    zone = edge_setback_zone(parcel, 0, 2)
    unit = math.sqrt(0.5)
    assert zone.covers(Point(5 - 1.9 * unit, 5 + 1.9 * unit))
    assert not zone.covers(Point(5 - 2.1 * unit, 5 + 2.1 * unit))
    # Beyond the selected segment endpoint, still within 2 feet of that endpoint.
    assert zone.covers(Point(9.5, 11))
    assert parcel.to_shape().covers(zone)


@pytest.mark.parametrize("status,code,severity", [
    ("proposed", "SITE_CONSTRAINT_VIOLATION", "ERROR"),
    ("existing", "EXISTING_SITE_CONSTRAINT_CONFLICT", "WARNING"),
])
def test_pool_overlap_is_scoped_and_source_assumption_visible(status, code, severity):
    p = project()
    p.existing_conditions.site_constraints = [SiteConstraint(id="rear", edge_index=2, distance_ft=10)]
    p.existing_conditions.hardscape = [HardscapeArea(id="pool", subtype="pool", status=status, geometry=rectangle(20, 85, 30, 95))]
    result = validate_project(p)
    assert any(m.code == code and m.severity == severity and m.entity_id == "pool" for m in result.messages)
    assert any(m.code == "SITE_CONSTRAINT_UNVERIFIED" for m in result.warnings)
    assert result.ok == (status == "existing")


def test_pool_constraint_does_not_restrict_beds_patios_or_touching_pool():
    p = project()
    p.existing_conditions.site_constraints = [SiteConstraint(id="rear", edge_index=2, distance_ft=10)]
    p.existing_conditions.hardscape = [
        HardscapeArea(id="patio", subtype="patio", status="proposed", geometry=rectangle(20, 91, 30, 99)),
        HardscapeArea(id="pool", subtype="pool", status="proposed", geometry=rectangle(40, 80, 50, 90)),
    ]
    p.existing_conditions.planting_beds = [PlantingBed(id="bed", status="proposed", geometry=rectangle(60, 91, 70, 99))]
    assert validate_project(p).ok


@pytest.mark.parametrize("values", [
    {}, {"edge_index": 0}, {"distance_ft": 6}, {"edge_index": -1, "distance_ft": 6},
    {"edge_index": 0, "distance_ft": 0}, {"edge_index": 0, "distance_ft": float("inf")},
    {"geometry": rectangle(0, 0, 1, 1), "edge_index": 0, "distance_ft": 6},
    {"geometry": rectangle(0, 0, 1, 1), "applies_to": []},
    {"geometry": rectangle(0, 0, 1, 1), "applies_to": [""]},
])
def test_invalid_constraint_schema_is_rejected(values):
    with pytest.raises(ValidationError):
        SiteConstraint(id="invalid", **values)


@pytest.mark.parametrize("constraint", [
    SiteConstraint(id="invalid", edge_index=8, distance_ft=6),
    SiteConstraint(id="invalid", geometry=polygon([(0, 0), (10, 10), (0, 10), (10, 0)])),
])
def test_invalid_constraint_geometry_reports_error_without_crashing(constraint):
    p = project()
    p.existing_conditions.site_constraints = [constraint]
    assert any(m.code == "INVALID_SITE_CONSTRAINT" for m in validate_project(p).errors)


def test_constraint_ids_and_sources_participate_validation():
    p = project()
    p.existing_conditions.site_constraints = [SiteConstraint(
        id="parcel", geometry=rectangle(0, 0, 10, 10), source=SourceInfo(reference="missing"),
    )]
    codes = {m.code for m in validate_project(p).errors}
    assert {"DUPLICATE_ENTITY_ID", "UNKNOWN_SOURCE_REFERENCE"} <= codes


@pytest.mark.parametrize("status,subtype,placement,ok", [
    ("existing", "fence", "context", True),
    ("existing", "fence", "on_site", False),
    ("proposed", "fence", "context", False),
    ("existing", "wall", "context", False),
])
def test_only_explicit_existing_context_fence_can_extend_outside(status, subtype, placement, ok):
    p = project()
    p.existing_conditions.linear_features = [LinearFeature(
        id="line", subtype=subtype, status=status, placement=placement,
        geometry=GeometryData(type="linestring", coordinates=[(-2, 0), (-2, 100)]),
    )]
    result = validate_project(p)
    assert result.ok == ok
    if ok:
        assert any(m.code == "EXISTING_FENCE_OUTSIDE_PARCEL" for m in result.warnings)


def test_concave_parcel_clipping_preserves_disconnected_zone_parts():
    parcel = polygon([(0, 0), (20, 0), (20, 2), (2, 2), (2, 8), (20, 8), (20, 10), (0, 10)])
    zone = edge_setback_zone(parcel, 1, 9)
    assert zone.geom_type == "MultiPolygon"
    assert len(zone.geoms) == 2
    assert parcel.to_shape().covers(zone)
    assert zone.covers(Point(19, 1))
    assert zone.covers(Point(19, 9))


def test_oblique_clipped_zones_do_not_fail_containment_due_to_roundoff():
    from shapely.affinity import rotate

    # Synthetic irregular quadrilateral with a tiny measured closure segment.
    ring = rotate(
        polygon([(0, 0), (4.2, 130.3), (94.7, 161.8), (89.2, 0.009), (0.003, 0.008)]).to_shape(),
        17.37, origin=(0, 0),
    )
    p = project()
    p.existing_conditions.parcel.boundary = polygon(list(ring.exterior.coords))
    p.existing_conditions.site_constraints = [
        SiteConstraint(id=f"edge-{index}", edge_index=index, distance_ft=distance)
        for index, distance in [(0, 6), (1, 10), (2, 6)]
    ]
    assert validate_project(p).ok


def test_real_explicit_zone_outside_area_still_fails():
    p = project()
    p.existing_conditions.site_constraints = [
        SiteConstraint(id="outside", geometry=rectangle(-0.01, 0, 10, 10)),
    ]
    assert any(m.code == "SITE_CONSTRAINT_OUTSIDE_PARCEL" for m in validate_project(p).errors)


@pytest.mark.parametrize("subtype,applies_to", [("Pool", ["pool"]), (" pool ", ["pool"]), ("pool", [" POOL "])])
def test_constraint_subtype_matching_ignores_case_and_outer_whitespace(subtype, applies_to):
    p = project()
    p.existing_conditions.site_constraints = [
        SiteConstraint(id="rear", edge_index=2, distance_ft=10, applies_to=applies_to),
    ]
    p.existing_conditions.hardscape = [
        HardscapeArea(id="pool", subtype=subtype, status="proposed", geometry=rectangle(20, 85, 30, 95)),
    ]
    assert any(m.code == "SITE_CONSTRAINT_VIOLATION" for m in validate_project(p).errors)
