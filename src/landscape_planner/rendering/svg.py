"""Deterministic SVG renderer for existing-conditions site plans."""

from __future__ import annotations

from html import escape
from pathlib import Path
import textwrap
from typing import Iterable

from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.geometry.base import BaseGeometry

from landscape_planner.model.project import LandscapeProject
from landscape_planner.analysis.constraints import constraint_shape

SVG_WIDTH = 1632
SVG_HEIGHT = 1056
MARGIN = 72
TITLEBLOCK_WIDTH = 300


def render_existing_conditions_svg(project: LandscapeProject, output_path: str | Path) -> Path:
    """Render an L1.0 existing-conditions SVG drawing."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(existing_conditions_svg(project), encoding="utf-8")
    return output


def existing_conditions_svg(project: LandscapeProject) -> str:
    """Return SVG text for the project's existing conditions."""

    conditions = project.existing_conditions
    parcel = conditions.parcel.boundary.to_shape()
    minx, miny, maxx, maxy = parcel.bounds
    drawing_width = SVG_WIDTH - (MARGIN * 2) - TITLEBLOCK_WIDTH
    drawing_height = SVG_HEIGHT - (MARGIN * 2)
    scale = min(drawing_width / (maxx - minx), drawing_height / (maxy - miny))

    def xy(x: float, y: float) -> tuple[float, float]:
        sx = MARGIN + (x - minx) * scale
        sy = MARGIN + (maxy - y) * scale
        return sx, sy

    elements: list[str] = [
        _svg_header(),
        '<rect class="sheet" x="0" y="0" width="1632" height="1056" />',
        '<g id="00_background"><rect class="drawing-area" x="72" y="72" '
        'width="1188" height="912" /></g>',
        '<g id="10_property">',
        _path(parcel, xy, "property-line", conditions.parcel.id),
        _label(parcel.centroid, xy, conditions.parcel.id, "label property-label"),
        "</g>",
        '<g id="20_existing_structures">',
    ]

    for structure in sorted(conditions.structures, key=lambda item: item.id):
        shape = structure.footprint.to_shape()
        elements.append(_path(shape, xy, "structure", structure.id))
        elements.append(_label(shape.centroid, xy, structure.name or structure.id, "label"))
    elements.append("</g>")

    elements.append('<g id="30_existing_hardscape">')
    for hardscape in sorted(conditions.hardscape, key=lambda item: item.id):
        shape = hardscape.geometry.to_shape()
        elements.append(_path(shape, xy, f"hardscape hardscape-{escape(hardscape.subtype)}", hardscape.id))
        elements.append(_label(shape.centroid, xy, hardscape.name or hardscape.subtype, "label small"))
    for feature in sorted(conditions.linear_features, key=lambda item: item.id):
        if feature.subtype == "fence":
            continue
        elements.append(_line(feature.geometry.to_shape(), xy, "linear-feature", feature.id))
        elements.append(_label(feature.geometry.to_shape().centroid, xy, feature.name or feature.id, "label tiny"))
    elements.append("</g>")

    elements.append('<g id="40_existing_vegetation">')
    for lawn in sorted(conditions.lawn, key=lambda item: item.id):
        shape = lawn.geometry.to_shape()
        elements.append(_path(shape, xy, "lawn", lawn.id))
        elements.append(_label(shape.centroid, xy, lawn.name or "Lawn", "label small"))
    for bed in sorted(conditions.planting_beds, key=lambda item: item.id):
        shape = bed.geometry.to_shape()
        elements.append(_path(shape, xy, "planting-bed", bed.id))
        elements.append(_label(shape.centroid, xy, bed.name or bed.id, "label small"))
    for tree in sorted(conditions.trees, key=lambda item: item.id):
        cx, cy = xy(tree.point.x, tree.point.y)
        radius = tree.canopy_radius_ft * scale
        elements.append(
            f'<g class="tree" id="{escape(tree.id)}" data-entity-id="{escape(tree.id)}">'
            f'<circle class="tree-canopy" cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(radius)}" />'
            f'<circle class="tree-trunk" cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(max(3, radius * 0.08))}" />'
            "</g>"
        )
        label = tree.common_name or tree.name or tree.id
        elements.append(_label(Point(tree.point.x, tree.point.y + tree.canopy_radius_ft), xy, label, "label tiny"))
    elements.append("</g>")

    elements.append('<g id="45_existing_utilities">')
    for utility in sorted(conditions.utilities, key=lambda item: item.id):
        clearance = utility.clearance_shape
        if clearance is not None and isinstance(clearance, Polygon):
            elements.append(_path(clearance, xy, "utility-clearance", f"{utility.id}_CLEARANCE"))
        shape = utility.shape
        if isinstance(shape, Point):
            elements.append(_utility_symbol(shape, xy, utility.id))
            label_point = Point(shape.x, shape.y + 3)
        elif isinstance(shape, LineString):
            elements.append(_line(shape, xy, "utility-line", utility.id))
            label_point = shape.centroid
        elif isinstance(shape, Polygon):
            elements.append(_path(shape, xy, "utility-area", utility.id))
            label_point = shape.centroid
        else:
            continue
        elements.append(_label(label_point, xy, utility.name or utility.utility_type, "label tiny"))
    elements.append("</g>")

    elements.append('<g id="50_site_constraints">')
    for constraint in sorted(conditions.site_constraints, key=lambda item: item.id):
        shape = constraint_shape(constraint, conditions.parcel.boundary)
        if not shape.is_empty:
            elements.append(_path(shape, xy, "site-constraint", constraint.id))
            scope = ", ".join(constraint.applies_to)
            label = f"{scope} exclusion"
            if constraint.distance_ft is not None:
                label += f" · {_fmt(constraint.distance_ft)} ft from property edge"
            elements.append(_label(shape.representative_point(), xy, label, "label tiny"))
    elements.append("</g>")
    # Fences are surveyed physical features, never a replacement parcel boundary.
    elements.append('<g id="55_existing_fences">')
    for feature in sorted(conditions.linear_features, key=lambda item: item.id):
        if feature.subtype == "fence":
            elements.append(_line(feature.geometry.to_shape(), xy, "fence", feature.id))
            elements.append(_label(feature.geometry.to_shape().centroid, xy,
                                   feature.name or feature.id, "label tiny"))
    elements.append("</g>")

    elements.extend(
        [
            '<g id="80_annotations">',
            _graphic_scale(MARGIN, SVG_HEIGHT - MARGIN + 22, scale),
            "</g>",
            '<g id="99_titleblock">',
            _title_block(project),
            _north_arrow(SVG_WIDTH - TITLEBLOCK_WIDTH + 78, 114, project.coordinate_system.north_rotation_degrees),
            "</g>",
            "</svg>",
        ]
    )
    return "\n".join(elements) + "\n"


def _svg_header() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="17in" height="11in" '
        'viewBox="0 0 1632 1056" role="img" aria-label="Existing conditions landscape plan">\n'
        "<defs>\n"
        "<style>\n"
        ".sheet{fill:#fbfaf7}.drawing-area{fill:#fffefa;stroke:#d2d0c8;stroke-width:1}"
        ".property-line{fill:none;stroke:#161616;stroke-width:3.2}"
        ".structure{fill:#d9d9d6;stroke:#2b2b2b;stroke-width:2.2}"
        ".hardscape{fill:#ece7df;stroke:#5f5a52;stroke-width:1.6}"
        ".hardscape-driveway{fill:#e0dfdc}.hardscape-patio{fill:#e8e1d4}"
        ".linear-feature{fill:none;stroke:#444;stroke-width:2;stroke-dasharray:8 5}"
        ".site-constraint{fill:#d92d32;fill-opacity:.22;stroke:#ae2026;stroke-width:2;stroke-dasharray:8 5;fill-rule:evenodd}"
        ".fence{fill:none;stroke:#803cad;stroke-width:3;stroke-dasharray:10 3}"
        ".lawn{fill:#dbe8cf;stroke:#73915d;stroke-width:1.2}"
        ".planting-bed{fill:#d7c8a6;stroke:#7d6d4c;stroke-width:1.4}"
        ".tree-canopy{fill:#bfd1ad;stroke:#40603c;stroke-width:1.4}"
        ".tree-trunk{fill:#735b3c;stroke:#40311f;stroke-width:0.8}"
        ".utility-clearance{fill:#f4ecd2;fill-opacity:.35;stroke:#9a7b22;stroke-width:1.2;stroke-dasharray:6 4}"
        ".utility-area{fill:#f0d9b5;stroke:#6f5620;stroke-width:1.5}"
        ".utility-line{fill:none;stroke:#6f5620;stroke-width:1.5;stroke-dasharray:4 4}"
        ".utility-symbol{fill:#fffefa;stroke:#6f5620;stroke-width:1.8}"
        ".utility-symbol-mark{stroke:#6f5620;stroke-width:1.8}"
        ".label{font-family:Arial,sans-serif;font-size:18px;fill:#1f1f1f;text-anchor:middle;"
        "paint-order:stroke;stroke:#fffefa;stroke-width:4px;stroke-linejoin:round}"
        ".small{font-size:15px}.tiny{font-size:13px}.property-label{font-weight:bold}"
        ".title{font-family:Arial,sans-serif;font-size:24px;font-weight:bold;fill:#111}"
        ".meta{font-family:Arial,sans-serif;font-size:16px;fill:#222}"
        ".rule{stroke:#111;stroke-width:1.4}.scale-text{font-family:Arial,sans-serif;font-size:13px;fill:#111}"
        "</style>\n"
        "</defs>"
    )


def _path(shape: BaseGeometry, xy, class_name: str, entity_id: str | None = None) -> str:
    if not isinstance(shape, (Polygon, MultiPolygon)):
        raise TypeError(f"Expected Polygon or MultiPolygon, got {shape.geom_type}")
    id_attr = f' id="{escape(entity_id)}" data-entity-id="{escape(entity_id)}"' if entity_id else ""
    if isinstance(shape, Polygon) and not shape.interiors:
        points = " ".join(_point(pair, xy) for pair in shape.exterior.coords)
        return f'<polygon{id_attr} class="{class_name}" points="{points}" />'
    polygons = [shape] if isinstance(shape, Polygon) else shape.geoms
    rings = []
    for polygon in polygons:
        for ring in [polygon.exterior, *polygon.interiors]:
            points = [_point(pair, xy) for pair in ring.coords]
            rings.append("M" + " L".join(points) + " Z")
    return f'<path{id_attr} class="{class_name}" d="{" ".join(rings)}" fill-rule="evenodd" />'


def _line(shape: BaseGeometry, xy, class_name: str, entity_id: str | None = None) -> str:
    if not isinstance(shape, LineString):
        raise TypeError(f"Expected LineString, got {shape.geom_type}")
    points = " ".join(_point(pair, xy) for pair in shape.coords)
    id_attr = f' id="{escape(entity_id)}" data-entity-id="{escape(entity_id)}"' if entity_id else ""
    return f'<polyline{id_attr} class="{class_name}" points="{points}" />'


def _point(pair: Iterable[float], xy) -> str:
    x, y = pair
    sx, sy = xy(float(x), float(y))
    return f"{_fmt(sx)},{_fmt(sy)}"


def _label(point: Point, xy, text: str, class_name: str) -> str:
    x, y = xy(point.x, point.y)
    return f'<text class="{class_name}" x="{_fmt(x)}" y="{_fmt(y)}">{escape(text)}</text>'


def _utility_symbol(point: Point, xy, entity_id: str) -> str:
    x, y = xy(point.x, point.y)
    return (
        f'<g class="utility" id="{escape(entity_id)}" data-entity-id="{escape(entity_id)}" transform="translate({_fmt(x)} {_fmt(y)})">'
        '<circle class="utility-symbol" cx="0" cy="0" r="8" />'
        '<line class="utility-symbol-mark" x1="-4" y1="-4" x2="4" y2="4" />'
        '<line class="utility-symbol-mark" x1="4" y1="-4" x2="-4" y2="4" />'
        "</g>"
    )


def _north_arrow(x: float, y: float, rotation: float = 0.0) -> str:
    return (
        f'<g class="north-arrow" transform="translate({_fmt(x)} {_fmt(y)}) rotate({_fmt(rotation)})">'
        '<path d="M0,-34 L13,20 L0,12 L-13,20 Z" fill="#111" />'
        '<line class="rule" x1="0" y1="20" x2="0" y2="48" />'
        '<text class="meta" x="0" y="72" text-anchor="middle">N</text>'
        "</g>"
    )


def _graphic_scale(x: float, y: float, scale: float) -> str:
    length_ft = 20
    length_px = length_ft * scale
    return (
        f'<g class="graphic-scale" transform="translate({_fmt(x)} {_fmt(y)})">'
        f'<line class="rule" x1="0" y1="0" x2="{_fmt(length_px)}" y2="0" />'
        '<line class="rule" x1="0" y1="-8" x2="0" y2="8" />'
        f'<line class="rule" x1="{_fmt(length_px)}" y1="-8" x2="{_fmt(length_px)}" y2="8" />'
        f'<text class="scale-text" x="{_fmt(length_px / 2)}" y="24" text-anchor="middle">20 ft</text>'
        "</g>"
    )


def _title_block(project: LandscapeProject) -> str:
    x = SVG_WIDTH - TITLEBLOCK_WIDTH + 24
    y = SVG_HEIGHT - 270
    location = ", ".join(
        item
        for item in [
            project.project.location.city,
            project.project.location.state,
            project.project.location.country,
        ]
        if item
    )
    return (
        f'<rect x="{SVG_WIDTH - TITLEBLOCK_WIDTH}" y="0" width="{TITLEBLOCK_WIDTH}" '
        'height="1056" fill="#f1efe8" stroke="#111" stroke-width="1.4" />'
        f'<line class="rule" x1="{SVG_WIDTH - TITLEBLOCK_WIDTH}" y1="{y - 24}" x2="1632" y2="{y - 24}" />'
        f'<text class="title" x="{x}" y="{y}">L1.0</text>'
        f'<text class="meta" x="{x}" y="{y + 34}">Existing Conditions</text>'
        + _title_meta(x, y + 78, project.project.name)
        + _title_meta(x, y + 122, f"Project ID: {project.project.id}")
        + f'<text class="meta" x="{x}" y="{y + 168}">Schema: {project.schema_version}</text>'
        + _title_meta(x, y + 194, location)
    )


def _title_meta(x: float, y: float, text: str) -> str:
    """Bound free text to two lines; keep the complete value in an SVG title."""
    lines = textwrap.wrap(text, width=28, max_lines=2, placeholder="…") or [""]
    elements = [f"<g><title>{escape(text)}</title>"]
    for index, line in enumerate(lines):
        # Conservative Arial 16px width estimate; unusual wide glyphs receive
        # a bounded textLength rather than spilling outside the sheet.
        width = sum(4.5 if c in " il.,:;'!|" else 16 if c in "MW@" or ord(c) > 127
                    else 11 if c.isupper() else 9 for c in line)
        fit = ' textLength="252" lengthAdjust="spacingAndGlyphs"' if width > 252 else ""
        elements.append(f'<text class="meta" x="{_fmt(x)}" y="{_fmt(y + index * 19)}"{fit}>{escape(line)}</text>')
    elements.append("</g>")
    return "".join(elements)


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")
