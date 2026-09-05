"""Contract tests for portable, deterministic and deliberately scoped HTML exports."""

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest

from landscape_planner.io.yaml_loader import load_project
from landscape_planner.rendering.html import (
    existing_conditions_html,
    render_existing_conditions_html,
)
from landscape_planner.rendering.svg import existing_conditions_svg


FIXTURE = Path("tests/fixtures/synthetic")


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def test_html_is_deterministic_and_self_contained():
    project = load_project(FIXTURE)
    first = existing_conditions_html(project)
    assert first == existing_conditions_html(project)
    parser = DocumentParser()
    parser.feed(first)
    assert any(tag == "svg" for tag, _ in parser.elements)
    assert not any(
        attrs.get("src") or (tag == "link" and attrs.get("href"))
        for tag, attrs in parser.elements
    )
    assert "@import" not in first
    assert "HOUSE001" in first
    assert "sqft" in first


def test_share_profile_omits_private_fields_from_entire_document():
    project = load_project(FIXTURE)
    project.project.id = "PRIVATE_PROJECT_ID_CANARY"
    project.project.name = "PRIVATE_PROJECT_NAME_CANARY"
    project.project.location.city = "PRIVATE_CITY_CANARY"
    project.coordinate_system.origin_description = "PRIVATE_ORIGIN_CANARY"
    project.existing_conditions.parcel.legal_notes = ["PRIVATE_LEGAL_CANARY"]
    project.existing_conditions.structures[0].notes = ["PRIVATE_NOTES_CANARY"]
    project.existing_conditions.structures[0].description = "PRIVATE_DESCRIPTION_CANARY"
    project.reference_documents[0].filename = "references/PRIVATE_FILENAME_CANARY.pdf"
    project.reference_documents[0].author = "PRIVATE_AUTHOR_CANARY"
    project.site_photos[0].filename = "references/PRIVATE_PHOTO_CANARY.jpg"
    project.site_photos[0].description = "PRIVATE_PHOTO_DESCRIPTION_CANARY"
    source = project.existing_conditions.parcel.source
    project.reference_documents[0].id = "PRIVATE_SOURCE_CANARY"
    source.reference = "PRIVATE_SOURCE_CANARY"

    document = existing_conditions_html(project, profile="share")
    assert "PRIVATE_" not in document
    assert "HOUSE001" in document
    assert "House" in document
    assert "medium" in document
    private = existing_conditions_html(project, profile="private")
    assert "PRIVATE_PROJECT_NAME_CANARY" in private
    assert "PRIVATE_NOTES_CANARY" in private
    assert "PRIVATE_SOURCE_CANARY" in private


@pytest.mark.parametrize("profile", ["share", "private"])
def test_hostile_labels_cannot_create_html_or_break_json(profile):
    project = load_project(FIXTURE)
    hostile = '</script><img src="https://invalid.example/x" onerror="alert(1)"> & \u2028\u2029'
    project.existing_conditions.structures[0].name = hostile
    document = existing_conditions_html(project, profile=profile)
    parser = DocumentParser()
    parser.feed(document)
    assert not any(tag == "img" for tag, _ in parser.elements)
    assert not any(
        key.startswith("on") for _, attrs in parser.elements for key in attrs
    )
    payload_match = re.search(r'<script[^>]*id="plan-data"[^>]*>(.*?)</script>', document, re.S)
    assert payload_match is not None
    payload = json.loads(payload_match.group(1))
    def string_values(value):
        if isinstance(value, dict):
            return [leaf for child in value.values() for leaf in string_values(child)]
        if isinstance(value, list):
            return [leaf for child in value for leaf in string_values(child)]
        return [value] if isinstance(value, str) else []

    assert hostile in string_values(payload)
    assert "<" not in payload_match.group(1)


def test_embedded_svg_preserves_canonical_geometry():
    project = load_project(FIXTURE)
    document = existing_conditions_html(project)
    embedded = re.search(r"<svg\b.*?</svg>", document, re.S)
    assert embedded is not None

    def geometry(svg):
        root = ET.fromstring(svg)
        fields = ("d", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "points", "width", "height")
        return [
            (element.tag, tuple((key, element.get(key)) for key in fields if key in element.attrib))
            for element in root.iter()
            if element.tag.rsplit("}", 1)[-1] in {"path", "circle", "line", "polyline", "polygon", "rect"}
        ]

    assert geometry(embedded.group()) == geometry(existing_conditions_svg(project))


def test_invalid_geometry_does_not_create_or_replace_output(tmp_path):
    project = load_project(FIXTURE)
    project.existing_conditions.structures[0].footprint.coordinates = [
        [200, 200], [210, 200], [210, 210], [200, 210]
    ]
    output = tmp_path / "plan.html"
    with pytest.raises(ValueError):
        render_existing_conditions_html(project, output)
    assert not output.exists()
    output.write_text("previous good export")
    with pytest.raises(ValueError):
        render_existing_conditions_html(project, output)
    assert output.read_text() == "previous good export"


def test_unknown_profile_fails_before_writing(tmp_path):
    output = tmp_path / "plan.html"
    with pytest.raises(ValueError):
        render_existing_conditions_html(load_project(FIXTURE), output, profile="public")
    assert not output.exists()


@pytest.mark.parametrize("rotation", [0, 37, -90])
def test_north_arrow_rotation_and_paint_order(rotation):
    project = load_project(FIXTURE)
    project.coordinate_system.north_rotation_degrees = rotation
    for document in (existing_conditions_svg(project), existing_conditions_html(project)):
        svg = re.search(r"<svg\b.*?</svg>", document, re.S).group()
        root = ET.fromstring(svg)
        nodes = list(root.iter())
        arrow = next(node for node in nodes if node.get("class") == "north-arrow")
        assert arrow.get("transform").endswith(f"rotate({rotation})")
        # The opaque title-block background must be painted before the arrow.
        title_block = next(node for node in nodes if arrow in list(node))
        title_background = next(node for node in title_block if node.tag.endswith("rect"))
        assert nodes.index(arrow) > nodes.index(title_background)


def test_provenance_is_available_in_static_markup():
    project = load_project(FIXTURE)
    project.existing_conditions.parcel.source.estimated_accuracy_ft = 0.5
    document = existing_conditions_html(project)
    static = re.sub(r"<script\b.*?</script>", "", document, flags=re.S)
    tables = re.findall(r"<table\b.*?</table>", static, re.S)
    provenance = next(table for table in tables if "Estimated accuracy" in table)
    assert "PARCEL001" in provenance
    assert "manual_estimate" in provenance
    assert "medium" in provenance
    assert "0.5 ft" in provenance
    assert "HOUSE001" in provenance
    assert "unknown" in provenance
