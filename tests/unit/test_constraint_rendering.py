"""Scoped exclusions stay distinguishable from property lines and actual fences."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from shapely.geometry import MultiPolygon, Polygon

from landscape_planner.inspection import find_entity, entity_inspection_payload
from landscape_planner.io.yaml_loader import load_project
from landscape_planner.model.project import LinearFeature, SiteConstraint
from landscape_planner.rendering.html import existing_conditions_html
from landscape_planner.rendering.svg import _path, existing_conditions_svg


def project_with_constraints():
    project = load_project(Path('tests/fixtures/synthetic'))
    project.existing_conditions.site_constraints = [SiteConstraint(
        id='POOL_REAR', name='Rear pool exclusion', edge_index=2, distance_ft=10,
        source={'type': 'manual_estimate', 'confidence': 'low', 'reference': 'PRIVATE_SURVEY_PATH'},
        notes=['PRIVATE_NOTE'],
    )]
    document = project.reference_documents[0].model_copy(deep=True)
    document.id = "PRIVATE_SURVEY_PATH"
    project.reference_documents.append(document)
    minx, miny, _, maxy = project.existing_conditions.parcel.boundary.to_shape().bounds
    project.existing_conditions.linear_features.append(LinearFeature(
        id='OFFSET_FENCE', subtype='fence', placement='context',
        geometry={'type': 'linestring', 'coordinates': [[minx - 1, miny + 5], [minx - 1, maxy - 5]]},
    ))
    return project


def test_scoped_layers_and_inspection_are_available_offline_and_private():
    project = project_with_constraints()
    document = existing_conditions_html(project)
    payload = json.loads(re.search(r'<script type="application/json" id="plan-data">(.*?)</script>', document).group(1))
    entity = next(e for e in payload['entities'] if e['id'] == 'POOL_REAR')
    assert entity['applies_to'] == ['pool']
    assert entity['confidence'] == 'low'
    assert any('10 ft' in value for value in entity['measurements'])
    assert 'PRIVATE_SURVEY_PATH' not in document
    assert 'PRIVATE_NOTE' not in document
    assert 'PRIVATE_SURVEY_PATH' in existing_conditions_html(project, 'private')
    assert 'pool only</td>' in document  # static scope table is readable without JS
    assert 'data-layer="plan-50_site_constraints"' in document
    assert 'data-layer="plan-55_existing_fences"' in document
    inspected = find_entity(project, 'POOL_REAR')
    assert inspected.category == 'site_constraint'
    assert entity_inspection_payload(inspected)['source']['distance_ft'] == 10


def test_fence_geometry_is_independent_and_nearby_context_is_on_sheet():
    project = project_with_constraints()
    svg = ET.fromstring(existing_conditions_svg(project))
    ns = {'s': 'http://www.w3.org/2000/svg'}
    fence = svg.find('.//s:g[@id="55_existing_fences"]/s:polyline[@id="OFFSET_FENCE"]', ns)
    assert fence is not None and fence.get('class') == 'fence'
    x = float(fence.get('points').split()[0].split(',')[0])
    boundary = svg.find('.//s:g[@id="10_property"]/s:polygon', ns)
    boundary_x = float(boundary.get('points').split()[0].split(',')[0])
    assert 0 < x < boundary_x
    assert svg.find('.//s:g[@id="50_site_constraints"]/*[@id="POOL_REAR"]', ns) is not None


def test_compound_constraint_paths_preserve_holes_and_disconnected_parts():
    hole = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)],
                   holes=[[(2, 2), (4, 2), (4, 4), (2, 4)]])
    shape = MultiPolygon([hole, Polygon([(20, 0), (22, 0), (22, 2), (20, 2)])])
    node = ET.fromstring(_path(shape, lambda x, y: (x, y), 'site-constraint', 'compound'))
    assert node.tag == 'path'
    assert node.get('fill-rule') == 'evenodd'
    assert node.get('d').count('M') == 3
    assert node.get('d').count('Z') == 3
