"""Geometry for supplied site constraints, independent of fence locations."""

from __future__ import annotations

import math

from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

from landscape_planner.model.geometry import GeometryData
from landscape_planner.model.project import SiteConstraint


def edge_setback_zone(
    parcel: GeometryData, edge_index: int, distance_ft: float,
) -> BaseGeometry:
    """Clip a distance-to-boundary-segment buffer to the parcel interior.

    Edge indices are zero based in the supplied polygon's exterior ring; the
    closing edge is included. Rounded ends include points near the endpoints
    on oblique parcels. No fence or inferred jurisdictional rule is used.
    Return Shapely geometry to preserve disconnected parts after clipping.
    """
    shape = parcel.to_shape()
    if shape.geom_type != "Polygon" or not shape.is_valid or shape.area <= 0:
        raise ValueError("Edge setbacks require a valid positive-area parcel polygon.")
    if not math.isfinite(distance_ft) or distance_ft <= 0:
        raise ValueError("Setback distance must be finite and positive.")
    vertices = list(shape.exterior.coords)
    if edge_index < 0 or edge_index >= len(vertices) - 1:
        raise ValueError(f"Edge index {edge_index} is outside the parcel's exterior ring.")
    edge = LineString(vertices[edge_index:edge_index + 2])
    if edge.length <= 0:
        raise ValueError("Selected parcel edge has zero length.")
    return shape.intersection(edge.buffer(distance_ft, quad_segs=32))


def constraint_shape(constraint: SiteConstraint, parcel: GeometryData) -> BaseGeometry:
    """Resolve the explicit polygon or selected parcel-edge exclusion zone."""
    if constraint.geometry is not None:
        return constraint.geometry.to_shape()
    return edge_setback_zone(parcel, constraint.edge_index, constraint.distance_ft)
