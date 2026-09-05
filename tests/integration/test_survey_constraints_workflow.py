"""Survey/course reporting and planning restrictions use the public CLI."""
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner
import yaml

from landscape_planner.cli.main import app
from landscape_planner.io.yaml_loader import load_project
from landscape_planner.planning.concepts import Concept, resolve_concept

RUNNER = CliRunner()


def test_survey_report_and_rejected_closure(tmp_path):
    source = Path('examples/constraints/traverse.yaml')
    result = RUNNER.invoke(app, ['survey', str(source)])
    assert result.exit_code == 0, (result.output, result.exception)
    report = json.loads(result.output)
    assert report['accepted'] and report['boundary']
    raw = yaml.safe_load(source.read_text())
    raw['legs'][-1]['distance_ft'] = 70
    wrong = tmp_path / 'traverse.yaml'
    wrong.write_text(yaml.safe_dump(raw))
    output = tmp_path / 'closure.json'
    result = RUNNER.invoke(app, ['survey', str(wrong), '-o', str(output)])
    assert result.exit_code == 1
    report = json.loads(output.read_text())
    assert not report['accepted'] and report['boundary'] is None
    assert report['closure_error_ft'] == pytest.approx(10)


def test_survey_refuses_alias_overwrite(tmp_path):
    source = tmp_path / 'traverse.yaml'
    source.write_bytes(Path('examples/constraints/traverse.yaml').read_bytes())
    original = source.read_bytes()
    alias = tmp_path / 'alias.json'
    alias.hardlink_to(source)
    result = RUNNER.invoke(app, ['survey', str(source), '-o', str(alias)])
    assert result.exit_code == 2
    assert source.read_bytes() == original


def test_constraints_fixture_can_render_and_compare(tmp_path):
    for command in ('render', 'compare'):
        arguments = [command, 'examples/constraints', '-o', str(tmp_path / f'{command}.html')]
        if command == 'render':
            arguments.extend(['--format', 'html'])
        result = RUNNER.invoke(app, arguments)
        assert result.exit_code == 0, (result.output, result.exception)
        assert 'REAR_POOL' in (tmp_path / f'{command}.html').read_text()


def test_concept_cannot_reuse_constraint_id():
    project = load_project('examples/constraints')
    concept = Concept(id='bad', name='Invalid identity', operations=[{
        'action':'add', 'category':'trees', 'entity_id':'REAR_POOL',
        'data':{'location':[5,90], 'canopy_radius_ft':2},
    }])
    with pytest.raises(ValueError, match='duplicate'):
        resolve_concept(project, concept)


def test_pool_constraint_violation_prevents_export_and_preserves_previous_output(tmp_path):
    raw = yaml.safe_load(Path('examples/constraints/planning.yaml').read_text())
    raw['concepts'] = [raw['concepts'][0]]
    raw['concepts'][0]['operations'][0]['data']['geometry']['coordinates'] = [[33,119],[53,119],[53,128],[33,128]]
    planning = tmp_path / 'planning.yaml'
    planning.write_text(yaml.safe_dump(raw))
    output = tmp_path / 'review.html'
    output.write_text('previous review')
    result = RUNNER.invoke(app, ['compare','examples/constraints','--planning',str(planning),'-o',str(output)])
    assert result.exit_code == 1
    assert 'REAR_POOL' in result.output
    assert output.read_text() == 'previous review'
