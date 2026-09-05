"""Offline browser contract for supplied pool constraints and actual fences."""
from pathlib import Path
import os

import pytest

from landscape_planner.io.yaml_loader import load_project
from landscape_planner.model.project import SiteConstraint, LinearFeature
from landscape_planner.rendering.html import render_existing_conditions_html

if os.environ.get('LANDSCAPE_REQUIRE_BROWSER') == '1':
    from playwright import sync_api as playwright
else:
    playwright = pytest.importorskip('playwright.sync_api')


@pytest.fixture
def browser():
    with playwright.sync_playwright() as runtime:
        try:
            instance = runtime.chromium.launch()
        except playwright.Error as exc:
            if "Executable doesn't exist" in str(exc):
                if os.environ.get('LANDSCAPE_REQUIRE_BROWSER') == '1':
                    pytest.fail('Required Chromium is absent; run: playwright install chromium')
                pytest.skip('Install Chromium with: playwright install chromium')
            raise
        yield instance
        instance.close()


def test_constraints_and_fence_layers_inspection_and_no_js(tmp_path, browser):
    project = load_project(Path('tests/fixtures/synthetic'))
    project.existing_conditions.site_constraints = [SiteConstraint(
        id='POOL_REAR', edge_index=2, distance_ft=10,
        source={'type': 'manual_estimate', 'confidence': 'low'},
    )]
    project.existing_conditions.linear_features.append(LinearFeature(
        id='FENCE_OFFSET', subtype='fence', placement='context',
        geometry={'type': 'linestring', 'coordinates': [[-1, 10], [-1, 50]]},
    ))
    output = render_existing_conditions_html(project, tmp_path / 'plan.html')
    context = browser.new_context(offline=True)
    page = context.new_page()
    page.goto(output.as_uri())
    for layer in ['50_site_constraints', '55_existing_fences']:
        toggle = page.locator(f'input[data-layer="plan-{layer}"]')
        assert page.locator(f'#plan-{layer}').is_visible()
        toggle.uncheck()
        assert not page.locator(f'#plan-{layer}').is_visible()
        toggle.check()
    page.locator('#entity-list button[data-entity-id="POOL_REAR"]').click()
    detail = page.locator('#inspector').inner_text()
    assert 'Excludes: pool only' in detail
    assert '10 ft' in detail and 'Confidence: low' in detail
    page.locator('#entity-list button[data-entity-id="FENCE_OFFSET"]').click()
    assert 'Placement: context' in page.locator('#inspector').inner_text()
    context.close()
    context = browser.new_context(offline=True, java_script_enabled=False)
    page = context.new_page()
    page.goto(output.as_uri())
    assert page.locator('#plan-50_site_constraints').is_visible()
    assert page.locator('#plan-55_existing_fences').is_visible()
    assert 'pool only' in page.locator('body').inner_text()
    context.close()
