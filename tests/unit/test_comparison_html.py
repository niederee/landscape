"""Comparison snapshots reconcile with core output and preserve privacy and frames."""
from html.parser import HTMLParser
from pathlib import Path

import pytest

from landscape_planner.estimating.quantities import format_quantity
from landscape_planner.io.yaml_loader import load_project
from landscape_planner.planning.concepts import compare_projects
from landscape_planner.rendering.comparison import comparison_html


class Parser(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def snapshots():
    base = load_project(Path('tests/fixtures/synthetic'))
    alternate = base.model_copy(deep=True)
    alternate.existing_conditions.trees = []
    alternate.existing_conditions.structures[0].name = 'Retained house'
    return [('existing', 'Baseline', base), ('option', 'Option A', alternate)]


def test_deterministic_offline_documents_with_core_differences_and_no_mutation():
    plans = snapshots()
    original = plans[0][2].model_dump_json()
    document = comparison_html(plans)
    assert document == comparison_html(plans)
    assert plans[0][2].model_dump_json() == original
    parser = Parser(document)
    frames = [attrs for tag, attrs in parser.elements if tag == 'iframe']
    assert len(frames) == 2
    assert all('srcdoc' in frame and 'src' not in frame for frame in frames)
    assert 'Proposed concept' in frames[1]['srcdoc']
    assert '· Existing conditions · Read-only' not in frames[1]['srcdoc']
    assert 'TREE001' in document and '<strong>Removed:</strong>' in document
    differences = compare_projects(plans[0][2], plans[1][2])
    for row in differences['quantity_deltas']:
        assert ''.join(f'<td>{format_quantity(row[key])}</td>' for key in ('before', 'after', 'delta')) in document
    for frame in frames:
        inner = Parser(frame['srcdoc'])
        ids = [attrs['id'] for _, attrs in inner.elements if 'id' in attrs]
        assert len(ids) == len(set(ids))
        assert 'Measurement provenance' in frame['srcdoc']


def test_private_data_not_embedded_and_hostile_titles_remain_text():
    plans = snapshots()
    hostile = '</iframe><script>alert(1)</script><img src="https://invalid.example">'
    for _, _, project in plans:
        project.project.name = 'PRIVATE_NAME_CANARY'
        project.existing_conditions.structures[0].notes = ['PRIVATE_NOTE_CANARY']
    plans[1] = ('option', hostile, plans[1][2])
    metadata = {'option': {'warnings': ['PRIVATE_WARNING_CANARY'], 'unexpected': 'PRIVATE_OTHER_CANARY'}}
    document = comparison_html(plans, metadata=metadata)
    assert all(canary not in document for canary in ['PRIVATE_NAME_CANARY', 'PRIVATE_NOTE_CANARY', 'PRIVATE_WARNING_CANARY', 'PRIVATE_OTHER_CANARY'])
    assert hostile not in document
    parser = Parser(document)
    assert not any(tag == 'img' for tag, _ in parser.elements)
    private = comparison_html(plans, profile='private', metadata=metadata)
    assert 'PRIVATE_NAME_CANARY' in private
    assert 'PRIVATE_NOTE_CANARY' in private
    assert 'PRIVATE_WARNING_CANARY' in private
    assert 'PRIVATE_OTHER_CANARY' not in private


def test_cumulative_cost_is_labeled_incomplete_with_unknowns_and_prerequisites():
    document = comparison_html(snapshots(), metadata={'option': {
        'cost': {'known_low': '100.00', 'known_high': '200.00', 'complete': False, 'unknown_item_ids': ['BED001']},
        'depends_on': ['prepare'], 'warnings': ['review rework'],
    }})
    assert 'Cumulative phase state' in document
    assert 'known subtotal; incomplete estimate' in document
    assert 'USD 100.00–200.00' in document
    assert 'Unknown cost items: BED001' in document
    assert 'Prerequisite phases: prepare' in document


def test_rejects_incomparable_frames_duplicate_ids_and_empty_input():
    plans = snapshots()
    plans[1][2].coordinate_system.north_rotation_degrees += 10
    with pytest.raises(ValueError, match='coordinate frame'):
        comparison_html(plans)
    with pytest.raises(ValueError, match='unique'):
        comparison_html([plans[0], plans[0]])
    with pytest.raises(ValueError, match='baseline'):
        comparison_html([])
    with pytest.raises(ValueError, match='profile'):
        comparison_html(snapshots(), profile='oops')


def test_source_validation_and_no_javascript_baseline_are_retained():
    document = comparison_html(snapshots(), project_root=Path('tests/fixtures/synthetic'))
    parser = Parser(document)
    cards = [attrs for tag, attrs in parser.elements if attrs.get('class') == 'snapshot']
    assert 'hidden' not in cards[0] and 'hidden' in cards[1]
    assert '<noscript>' in document
    frames = [attrs['srcdoc'] for tag, attrs in parser.elements if tag == 'iframe']
    assert all('REF_DOC_MISSING' in doc or 'REFERENCE' in doc for doc in frames)


def test_cost_items_show_scope_and_rates_without_leaking_private_source():
    metadata = {'option': {'cost_items': [
        {'id': 'bed', 'name': 'New bed', 'quantity': 12, 'unit': 'sqft',
         'rate_low': 2, 'rate_high': 4, 'source': 'PRIVATE_QUOTE_CANARY'},
        {'id': 'irrigation', 'quantity': 1, 'unit': 'allowance', 'rate_low': None, 'rate_high': None},
    ]}}
    public = comparison_html(snapshots(), metadata=metadata)
    assert 'PRIVATE_QUOTE_CANARY' not in public
    assert 'Sourced allowance' in public
    assert '<td>24–48</td>' in public
    assert '<td>2–4</td>' in public
    assert '<td>unknown</td>' in public
    assert 'not a complete project quote' in public
    private = comparison_html(snapshots(), profile='private', metadata=metadata)
    assert 'PRIVATE_QUOTE_CANARY' in private
